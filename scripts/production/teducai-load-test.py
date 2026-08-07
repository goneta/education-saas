#!/usr/bin/env python3
"""Test de charge « journée de rentrée » — À EXÉCUTER SUR L'ENVIRONNEMENT RÉEL.

Pourquoi pas en local : ce test ne dit la vérité que contre PostgreSQL, sur la
machine de production, derrière le même reverse proxy. Sur un poste de
développement (SQLite, un seul processus uvicorn) il mesure surtout le disque du
poste — un résultat rassurant y serait trompeur.

Ce qu'il simule : le pic réel d'une rentrée — des dizaines de connexions
simultanées, puis les écrans que tout le monde ouvre en même temps (tableau de
bord, liste des élèves, emploi du temps, appel, notes).

Usage :
    export TEDUCAI_URL=https://teducai.com
    export TEDUCAI_USERS="admin@ecole.ci:MotDePasse123!,prof@ecole.ci:Autre123!"
    python scripts/production/teducai-load-test.py --concurrency 50 --duration 60

Le script n'écrit RIEN : il n'appelle que des endpoints de lecture.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time
from collections import Counter, defaultdict

try:
    import httpx
except ImportError:  # pragma: no cover
    sys.exit("httpx est requis : pip install httpx")


# Écrans réellement ouverts en masse un jour de rentrée (lectures seules).
READ_ENDPOINTS = [
    "/dashboard/summary",
    "/students?limit=50",
    "/education/classes",
    "/education/timetables",
    "/attendance/?limit=50",
    "/grades/assessments?limit=50",
    "/system/active-context",
]


async def login(client: httpx.AsyncClient, base: str, email: str, password: str) -> str | None:
    try:
        response = await client.post(
            f"{base}/auth/token",
            data={"username": email, "password": password},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        print(f"  [!] login {email} -> HTTP {response.status_code}")
    except Exception as exc:
        print(f"  [!] login {email} -> {exc.__class__.__name__}: {exc}")
    return None


async def worker(client, base, token, deadline, latencies, statuses, endpoint_latencies):
    headers = {"Authorization": f"Bearer {token}"}
    index = 0
    while time.monotonic() < deadline:
        endpoint = READ_ENDPOINTS[index % len(READ_ENDPOINTS)]
        index += 1
        started = time.perf_counter()
        try:
            response = await client.get(f"{base}{endpoint}", headers=headers, timeout=30)
            code = response.status_code
        except Exception as exc:
            code = exc.__class__.__name__
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies.append(elapsed_ms)
        endpoint_latencies[endpoint].append(elapsed_ms)
        statuses[code] += 1


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(len(ordered) * pct / 100), len(ordered) - 1)
    return ordered[index]


async def main() -> int:
    parser = argparse.ArgumentParser(description="Test de charge TeducAI (lecture seule)")
    parser.add_argument("--concurrency", type=int, default=50, help="clients simultanés")
    parser.add_argument("--duration", type=int, default=60, help="durée en secondes")
    parser.add_argument("--p95-budget-ms", type=float, default=800.0,
                        help="objectif p95 ; au-delà le script sort en échec")
    args = parser.parse_args()

    base = (os.getenv("TEDUCAI_URL") or "").rstrip("/")
    accounts = [pair for pair in (os.getenv("TEDUCAI_USERS") or "").split(",") if ":" in pair]
    if not base or not accounts:
        return int(bool(sys.stderr.write(
            "TEDUCAI_URL et TEDUCAI_USERS (email:motdepasse,...) sont requis.\n")) or 2)

    print(f"Cible      : {base}")
    print(f"Charge     : {args.concurrency} clients pendant {args.duration}s (lectures seules)")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("Connexion des comptes de test…")
        tokens = []
        for pair in accounts:
            email, _, password = pair.partition(":")
            token = await login(client, base, email.strip(), password.strip())
            if token:
                tokens.append(token)
        if not tokens:
            return int(bool(sys.stderr.write("Aucune connexion réussie — test interrompu.\n")) or 2)
        print(f"  {len(tokens)} compte(s) connecté(s)\n")

        latencies: list[float] = []
        statuses: Counter = Counter()
        endpoint_latencies: dict[str, list[float]] = defaultdict(list)
        deadline = time.monotonic() + args.duration
        started = time.monotonic()

        await asyncio.gather(*[
            worker(client, base, tokens[i % len(tokens)], deadline,
                   latencies, statuses, endpoint_latencies)
            for i in range(args.concurrency)
        ])
        elapsed = time.monotonic() - started

    total = len(latencies)
    errors = sum(count for code, count in statuses.items() if not (isinstance(code, int) and code < 400))
    print("=" * 62)
    print(f"Requêtes      : {total}  ({total / elapsed:.1f} req/s sur {elapsed:.0f}s)")
    print(f"Erreurs       : {errors} ({errors / total * 100:.2f} %)" if total else "Aucune requête")
    if latencies:
        print(f"Latence (ms)  : p50={percentile(latencies, 50):.0f}  "
              f"p95={percentile(latencies, 95):.0f}  p99={percentile(latencies, 99):.0f}  "
              f"max={max(latencies):.0f}  moyenne={statistics.mean(latencies):.0f}")
    print("\nDétail par écran (p95 ms) :")
    for endpoint, values in sorted(endpoint_latencies.items(), key=lambda kv: -percentile(kv[1], 95)):
        print(f"  {percentile(values, 95):7.0f}  {endpoint}")
    print("\nCodes de réponse :", dict(statuses))

    p95 = percentile(latencies, 95)
    verdict_ok = errors == 0 and p95 <= args.p95_budget_ms
    print("=" * 62)
    print("VERDICT : " + (
        f"OK — p95 {p95:.0f} ms sous le budget de {args.p95_budget_ms:.0f} ms, aucune erreur."
        if verdict_ok else
        f"À INVESTIGUER — p95 {p95:.0f} ms (budget {args.p95_budget_ms:.0f} ms), {errors} erreur(s)."
    ))
    return 0 if verdict_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
