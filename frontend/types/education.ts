export enum AssessmentType {
    EXAM = 'exam',
    HOMEWORK = 'homework',
    QUIZ = 'quiz',
    PROJECT = 'project',
    PARTICIPATION = 'participation'
}

export interface Term {
    id: number;
    name: string;
    start_date?: string;
    end_date?: string;
    academic_year_id: number;
}

export interface AcademicYear {
    id: number;
    name: string;
    start_date?: string;
    end_date?: string;
    is_current: boolean;
    terms: Term[];
}

export interface Assessment {
    id: number;
    title: string;
    type: AssessmentType;
    date: string;
    max_score: number;
    weight: number;
    class_id: number;
    subject_id: number;
    term_id: number;
}

export interface Grade {
    id: number;
    score: number;
    comment?: string;
    assessment_id: number;
    student_id: number;
}

export interface GradeBulkCreate {
    assessment_id: number;
    grades: {
        student_id: number;
        score: number;
        comment?: string;
    }[];
}
