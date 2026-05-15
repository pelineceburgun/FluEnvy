'use client';

import { useState } from 'react';

export default function Home() {
  const [studentText, setStudentText] = useState('');
  const [taskPrompt, setTaskPrompt] = useState('Some people believe that the best way to increase happiness is to spend money on experiences rather than possessions. Others disagree. Which do you prefer?');
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setFeedback('');

    try {
      const res = await fetch('http://localhost:8001/api/v1/feedback/writing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_text: studentText,
          task_prompt: taskPrompt,
          exam: 'TOEFL'
        }),
      });

      const data = await res.json();
      setFeedback(data.feedback || 'No feedback received');
    } catch (error) {
      setFeedback('Error: Could not connect to backend. Make sure FastAPI is running on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-blue-700">
          TOEFL & TELC AI Writing Feedback
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Task Prompt</label>
            <textarea
              value={taskPrompt}
              onChange={(e) => setTaskPrompt(e.target.value)}
              className="w-full h-24 p-4 border rounded-lg"
              placeholder="Task prompt..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Your Essay</label>
            <textarea
              value={studentText}
              onChange={(e) => setStudentText(e.target.value)}
              className="w-full h-48 p-4 border rounded-lg"
              placeholder="Write your essay here..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !studentText.trim()}
            className="w-full bg-blue-600 text-white py-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Generating Feedback...' : 'Get AI Feedback'}
          </button>
        </form>

        {feedback && (
          <div className="mt-8 p-6 bg-white border rounded-xl shadow">
            <h2 className="text-xl font-semibold mb-4">AI Feedback</h2>
            <div className="prose max-w-none whitespace-pre-wrap">
              {feedback}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}