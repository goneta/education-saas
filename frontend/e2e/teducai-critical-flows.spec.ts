import { test, expect, type APIRequestContext, type APIResponse, type Page } from '@playwright/test';

const API_URL = process.env.E2E_API_URL || 'http://127.0.0.1:8000';
const LOCALE = process.env.E2E_LOCALE || 'en';

type AuthContext = {
  email: string;
  password: string;
  token: string;
  headers: Record<string, string>;
};

type ApiEntity = Record<string, unknown> & { id: number };

type NamedEntity = ApiEntity & { name: string };
type PersonEntity = ApiEntity & { full_name: string };
type TitledEntity = ApiEntity & { title: string };

type CoreAcademicData = {
  teacher: PersonEntity;
  classRoom: NamedEntity;
  subject: NamedEntity;
  academicYear: NamedEntity;
  term: NamedEntity;
  student: PersonEntity;
  timetable: ApiEntity;
};

type SeededData = CoreAcademicData & {
  suffix: string;
  auth: AuthContext;
  assessment: TitledEntity;
  fee: TitledEntity;
  expense: TitledEntity;
  book: TitledEntity;
  loan: ApiEntity;
};

async function expectApiOk(response: APIResponse, context: string): Promise<void> {
  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`${context} failed with ${response.status()} ${response.statusText()}\n${body}`);
  }
}

async function apiJson<T = ApiEntity>(response: APIResponse, context: string): Promise<T> {
  await expectApiOk(response, context);
  return (await response.json()) as T;
}

function isoDate(daysFromToday = 0): string {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + daysFromToday);
  return date.toISOString();
}

function shortDate(daysFromToday = 0): string {
  return isoDate(daysFromToday).slice(0, 10);
}

async function bootstrapSchoolAndLogin(request: APIRequestContext, suffix: string): Promise<AuthContext> {
  const email = process.env.E2E_ADMIN_EMAIL || `admin.${suffix}@example.com`;
  const password = process.env.E2E_ADMIN_PASSWORD || 'Admin123!Secure';

  if (!process.env.E2E_ADMIN_EMAIL) {
    const register = await request.post(`${API_URL}/auth/register/school`, {
      data: {
        school: {
          name: `TeducAI E2E School ${suffix}`,
          domain_prefix: `e2e-${suffix}`,
          school_type: 'general',
          address: 'E2E automation address',
        },
        owner: {
          email,
          full_name: 'TeducAI E2E Admin',
          password,
          role: 'school_admin',
        },
      },
    });
    await expectApiOk(register, 'Register school and admin user');
  }

  const login = await request.post(`${API_URL}/auth/token`, {
    form: {
      username: email,
      password,
    },
  });
  const tokenResponse = await apiJson<{ access_token: string }>(login, 'Login through API');

  return {
    email,
    password,
    token: tokenResponse.access_token,
    headers: {
      Authorization: `Bearer ${tokenResponse.access_token}`,
    },
  };
}

async function createCoreAcademicData(request: APIRequestContext, suffix: string, auth: AuthContext): Promise<CoreAcademicData> {
  const teacher = await apiJson(
    await request.post(`${API_URL}/teachers/`, {
      headers: auth.headers,
      data: {
        email: `teacher.${suffix}@example.com`,
        full_name: `Teacher ${suffix}`,
        password: 'Teacher123!Secure',
        role: 'teacher',
        phone_number: '+2250700000001',
        address: 'Teacher E2E address',
        profile: {
          specialization: 'Mathematics',
          join_date: isoDate(-10),
          bio: 'Created by Playwright E2E test.',
        },
      },
    }),
    'Create teacher',
  );

  const classRoom = await apiJson(
    await request.post(`${API_URL}/education/classes`, {
      headers: auth.headers,
      data: {
        name: `Class ${suffix}`,
        level: 'Grade 7',
        main_teacher_id: teacher.id,
      },
    }),
    'Create class',
  );

  const subject = await apiJson(
    await request.post(`${API_URL}/education/subjects`, {
      headers: auth.headers,
      data: {
        name: `Mathematics ${suffix}`,
        code: `MATH-${suffix}`,
        description: 'E2E mathematics subject',
        coefficient: 2,
      },
    }),
    'Create subject',
  );

  const academicYear = await apiJson(
    await request.post(`${API_URL}/education/academic-years`, {
      headers: auth.headers,
      data: {
        name: `E2E ${suffix}`,
        start_date: isoDate(-30),
        end_date: isoDate(300),
        is_current: true,
      },
    }),
    'Create academic year',
  );

  const term = await apiJson(
    await request.post(`${API_URL}/education/terms`, {
      headers: auth.headers,
      data: {
        name: `Term ${suffix}`,
        start_date: isoDate(-20),
        end_date: isoDate(90),
        academic_year_id: academicYear.id,
      },
    }),
    'Create term',
  );

  const student = await apiJson(
    await request.post(`${API_URL}/students/`, {
      headers: auth.headers,
      data: {
        email: `student.${suffix}@example.com`,
        full_name: `Student ${suffix}`,
        password: 'Student123!Secure',
        role: 'student',
        profile: {
          registration_number: `REG-${suffix}`,
          date_of_birth: isoDate(-3650),
          gender: 'Male',
          student_address: 'Student E2E address',
          parent_name: 'Parent E2E',
          parent_phone: '+2250700000002',
          parent_email: `parent.${suffix}@example.com`,
          parent_address: 'Parent E2E address',
          current_class_id: classRoom.id,
        },
      },
    }),
    'Create student',
  );

  const timetable = await apiJson(
    await request.post(`${API_URL}/education/timetables`, {
      headers: auth.headers,
      data: {
        day_of_week: 'monday',
        start_time: '09:00:00',
        end_time: '10:00:00',
        room: 'Room E2E',
        class_id: classRoom.id,
        subject_id: subject.id,
        teacher_id: teacher.id,
      },
    }),
    'Create timetable entry',
  );

  return { teacher, classRoom, subject, academicYear, term, student, timetable };
}

async function createAcademicResults(request: APIRequestContext, suffix: string, auth: AuthContext, data: CoreAcademicData): Promise<{ assessment: TitledEntity; report: Record<string, unknown> }> {
  const assessment = await apiJson(
    await request.post(`${API_URL}/grades/assessments`, {
      headers: auth.headers,
      data: {
        title: `Assessment ${suffix}`,
        type: 'exam',
        date: isoDate(0),
        max_score: 20,
        weight: 2,
        class_id: data.classRoom.id,
        subject_id: data.subject.id,
        term_id: data.term.id,
      },
    }),
    'Create assessment',
  );

  await expectApiOk(
    await request.post(`${API_URL}/grades/entry/bulk`, {
      headers: auth.headers,
      data: {
        assessment_id: assessment.id,
        grades: [
          {
            assessment_id: assessment.id,
            student_id: data.student.id,
            score: 17.5,
            comment: 'Strong E2E result',
          },
        ],
      },
    }),
    'Enter grades in bulk',
  );

  const report = await apiJson(
    await request.get(`${API_URL}/grades/reports/student/${data.student.id}/term/${data.term.id}`, {
      headers: auth.headers,
    }),
    'Generate student report card',
  );

  return { assessment, report };
}

async function createAttendance(request: APIRequestContext, auth: AuthContext, data: CoreAcademicData): Promise<Record<string, unknown>> {
  return apiJson(
    await request.post(`${API_URL}/attendance/batch`, {
      headers: auth.headers,
      data: {
        timetable_id: data.timetable.id,
        date: shortDate(0),
        students: [
          {
            student_id: data.student.id,
            status: 'present',
            remarks: 'Present during E2E validation',
          },
        ],
      },
    }),
    'Record attendance',
  );
}

async function createFinanceData(request: APIRequestContext, suffix: string, auth: AuthContext, data: CoreAcademicData): Promise<{ fee: TitledEntity; expense: TitledEntity }> {
  const fee = await apiJson(
    await request.post(`${API_URL}/finance/fees`, {
      headers: auth.headers,
      data: {
        title: `Tuition ${suffix}`,
        amount: 500,
        due_date: isoDate(30),
        status: 'pending',
        description: 'E2E tuition fee',
        student_id: data.student.id,
      },
    }),
    'Create fee',
  );

  const paidFee = await apiJson(
    await request.post(`${API_URL}/finance/fees/${fee.id}/payments`, {
      headers: auth.headers,
      data: {
        amount: 200,
      },
    }),
    'Record fee payment',
  );

  const expense = await apiJson(
    await request.post(`${API_URL}/finance/expenses`, {
      headers: auth.headers,
      data: {
        title: `Books expense ${suffix}`,
        amount: 120,
        category: 'supplies',
        expense_date: isoDate(0),
        description: 'E2E school supplies expense',
      },
    }),
    'Create expense',
  );

  return { fee: paidFee, expense };
}

async function createLibraryData(request: APIRequestContext, suffix: string, auth: AuthContext, data: CoreAcademicData): Promise<{ book: TitledEntity; loan: ApiEntity }> {
  const book = await apiJson(
    await request.post(`${API_URL}/library/books`, {
      headers: auth.headers,
      data: {
        title: `E2E Book ${suffix}`,
        author: 'TeducAI Automation',
        isbn: `ISBN-${suffix}`,
        category: 'Testing',
        quantity: 3,
        location: 'Shelf E2E',
      },
    }),
    'Create library book',
  );

  const loan = await apiJson(
    await request.post(`${API_URL}/library/loans`, {
      headers: auth.headers,
      data: {
        book_id: book.id,
        user_id: data.student.id,
        due_date: isoDate(14),
        notes: 'E2E loan',
      },
    }),
    'Issue library loan',
  );

  const returnedLoan = await apiJson(
    await request.put(`${API_URL}/library/loans/${loan.id}/return`, {
      headers: auth.headers,
    }),
    'Return library loan',
  );

  return { book, loan: returnedLoan };
}

async function verifyAiChat(request: APIRequestContext, auth: AuthContext) {
  const response = await apiJson(
    await request.post(`${API_URL}/chat/`, {
      headers: auth.headers,
      data: {
        message: 'Give one short practical suggestion to support a parent whose child has attendance issues.',
      },
    }),
    'Call AI chat endpoint',
  );

  expect(response).toHaveProperty('message');
  expect(String(response.message).length).toBeGreaterThan(0);
  return response;
}

async function loginThroughUi(page: Page, auth: AuthContext) {
  await page.goto(`/${LOCALE}/login`);
  // Locate by stable ids / structure instead of the translated submit label
  // ("Log in" / "Se connecter" / …) — a text-based locator is brittle across
  // locales and builds. The login form is the one containing the password field;
  // the email/password inputs have stable ids.
  const loginForm = page.locator('form:has(#password)');
  await loginForm.waitFor({ state: 'visible' });
  await page.locator('#email').fill(auth.email);
  await page.locator('#password').fill(auth.password);
  await loginForm.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(new RegExp(`/${LOCALE}/dashboard`));
  await expect.poll(async () => page.evaluate(() => localStorage.getItem('access_token'))).toBeTruthy();
}

async function expectTextOnPage(page: Page, path: string, text: string) {
  await page.goto(`/${LOCALE}${path}`);
  await expect(page.getByText(text, { exact: false }).first()).toBeVisible();
}

test.describe('TeducAI critical end-to-end school workflows', () => {
  test('validates registration, login, academics, attendance, grades, finance, library, report card and AI chat', async ({ page, request }) => {
    const suffix = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

    const auth = await bootstrapSchoolAndLogin(request, suffix);
    await loginThroughUi(page, auth);

    const academicData = await createCoreAcademicData(request, suffix, auth);
    const { assessment } = await createAcademicResults(request, suffix, auth, academicData);
    await createAttendance(request, auth, academicData);
    const financeData = await createFinanceData(request, suffix, auth, academicData);
    const libraryData = await createLibraryData(request, suffix, auth, academicData);
    const aiResponse = await verifyAiChat(request, auth);

    const seeded: SeededData = {
      suffix,
      auth,
      ...academicData,
      assessment,
      fee: financeData.fee,
      expense: financeData.expense,
      book: libraryData.book,
      loan: libraryData.loan,
    };

    await expectTextOnPage(page, '/dashboard/students', seeded.student.full_name);
    await expectTextOnPage(page, '/dashboard/teachers', seeded.teacher.full_name);
    await expectTextOnPage(page, '/dashboard/education/classes', seeded.classRoom.name);
    await expectTextOnPage(page, '/dashboard/education/subjects', seeded.subject.name);
    await expectTextOnPage(page, '/dashboard/education/timetable', seeded.classRoom.name);
    await expectTextOnPage(page, '/dashboard/grades/assessments', seeded.assessment.title);
    await expectTextOnPage(page, '/dashboard/finance/fees', seeded.fee.title);
    await expectTextOnPage(page, '/dashboard/finance/expenses', seeded.expense.title);
    await expectTextOnPage(page, '/dashboard/library', seeded.book.title);

    await page.goto(`/${LOCALE}/dashboard/attendance/reports`);
    await expect(page.getByText(/Attendance|Report|Statistics/i).first()).toBeVisible();

    await page.goto(`/${LOCALE}/dashboard/grades/reports`);
    await expect(page.getByText(/Report|Student|Term/i).first()).toBeVisible();

    expect(String(aiResponse.message).length).toBeGreaterThan(0);
  });
});
