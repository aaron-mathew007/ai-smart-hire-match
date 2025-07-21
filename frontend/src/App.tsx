import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const App: React.FC = () => {
  const [resume, setResume] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState<File | null>(null);
  const [matchScore, setMatchScore] = useState<number | null>(null);
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);

  const handleResumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setResume(e.target.files[0]);
  };

  const handleJobDescriptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setJobDescription(e.target.files[0]);
  };

  const handleSubmit = async () => {
    try {
      // Upload resume
      const resumeFormData = new FormData();
      resumeFormData.append('file', resume!);
      const resumeResponse = await axios.post('http://localhost:8000/parse-resume', resumeFormData);
      setResumeId(resumeResponse.data.resume_id);

      // Upload job description
      const jdFormData = new FormData();
      jdFormData.append('file', jobDescription!);
      const jdResponse = await axios.post('http://localhost:8000/analyze-jd', jdFormData);
      setJobId(jdResponse.data.job_id);

      // Get match score
      const matchResponse = await axios.post('http://localhost:8000/match', { resume_id: resumeId, job_id: jobId });
      setMatchScore(matchResponse.data.score);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="container">
      <h1>AI-Powered Job Matching Platform</h1>
      <input type="file" onChange={handleResumeChange} accept=".pdf,.docx" />
      <input type="file" onChange={handleJobDescriptionChange} accept=".pdf,.docx" />
      <button onClick={handleSubmit}>Get Match Score</button>
      {matchScore && <p>Match Score: {matchScore.toFixed(2)}</p>}
    </div>
  );
};

export default App;
