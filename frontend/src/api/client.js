/**
 * API client for PGAGI Candidate Screening Backend
 */

const API_BASE = '/api/v1';

export async function uploadResumeFile(file, candidateName = '', email = '', phone = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (candidateName) formData.append('candidate_name', candidateName);
  if (email) formData.append('email', email);
  if (phone) formData.append('phone', phone);

  const response = await fetch(`${API_BASE}/resume/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Failed to upload and parse resume');
  }

  return response.json();
}

export async function parseResumeText(rawText, candidateName = '', email = '', fileName = 'sample_resume.txt') {
  const response = await fetch(`${API_BASE}/resume/parse-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      raw_text: rawText,
      candidate_name: candidateName || undefined,
      email: email || undefined,
      file_name: fileName,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Parsing failed' }));
    throw new Error(err.detail || 'Failed to parse resume text');
  }

  return response.json();
}

export async function getSupportedRoles() {
  const response = await fetch(`${API_BASE}/rag/roles`);
  if (!response.ok) throw new Error('Failed to fetch supported roles');
  return response.json();
}

export async function startInterviewSession(resumeId, targetRole, difficultyLevel = 'intermediate', totalQuestions = 5) {
  const response = await fetch(`${API_BASE}/interview/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume_id: resumeId,
      target_role: targetRole,
      difficulty_level: difficultyLevel,
      total_questions: totalQuestions,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to start interview' }));
    throw new Error(err.detail || 'Failed to start interview session');
  }

  return response.json();
}

export async function submitAnswer(sessionId, questionId, answerText) {
  const response = await fetch(`${API_BASE}/interview/${sessionId}/submit-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: questionId,
      answer_text: answerText,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to evaluate answer' }));
    throw new Error(err.detail || 'Failed to evaluate answer');
  }

  return response.json();
}

export async function getEvaluationReport(sessionId) {
  const response = await fetch(`${API_BASE}/evaluation/${sessionId}/report`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to fetch report' }));
    throw new Error(err.detail || 'Failed to fetch evaluation report');
  }
  return response.json();
}

export async function queryRAGInspector(query, role) {
  const response = await fetch(`${API_BASE}/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, role, top_k: 3 }),
  });
  if (!response.ok) throw new Error('Failed to query knowledge base');
  return response.json();
}

export async function checkSystemHealth() {
  const response = await fetch('/health');
  if (!response.ok) throw new Error('System unhealthy');
  return response.json();
}
