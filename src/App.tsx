import React, { useState, useRef } from 'react';
import { ValidatorReport, SimulationReport, AppState } from './types';
import { 
  CloudArrowUpIcon, 
  BeakerIcon, 
  PlayIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  DocumentTextIcon,
  VideoCameraIcon
} from '@heroicons/react/24/outline';

// Mock API Call functions (Replace with actual fetch calls to backend/app.py in production)
const api = {
  uploadAndValidate: async (file: File): Promise<ValidatorReport> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // In a real scenario: const response = await fetch('http://localhost:5000/validate', { method: 'POST', body: formData });
    // return response.json();

    // Mock delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Mock response based on task requirements
    return {
      passed: true,
      score: 85,
      package_name: "my_robot_controller",
      node_name: "pick_place_node",
      errors: [],
      warnings: ["While loop detected without rate limiting (line 45)"],
      details: {
        has_package_xml: true,
        has_build_file: true,
        node_type: 'ROS 2',
        publishers: ['/joint_trajectory_controller/follow_joint_trajectory'],
        subscribers: ['/joint_states']
      }
    };
  },
  runSimulation: async (pkg: string, node: string): Promise<SimulationReport> => {
    // In a real scenario: await fetch('http://localhost:5000/simulate', ...)
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    return {
      success: true,
      message: "Cube successfully reached target zone within tolerance.",
      logs: "[INFO] [launch]: All systems go\n[INFO] [spawn_entity]: Cube spawned\n[INFO] [controller]: Goal accepted\n[INFO] [checker]: End effector reached (0.0, 0.5, 0.2)",
      screenshot_url: "https://picsum.photos/600/400" // Placeholder
    };
  }
};

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.IDLE);
  const [file, setFile] = useState<File | null>(null);
  const [validationReport, setValidationReport] = useState<ValidatorReport | null>(null);
  const [simulationReport, setSimulationReport] = useState<SimulationReport | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setState(AppState.IDLE);
      setValidationReport(null);
      setSimulationReport(null);
    }
  };

  const startValidation = async () => {
    if (!file) return;
    setState(AppState.VALIDATING);
    try {
      const report = await api.uploadAndValidate(file);
      setValidationReport(report);
      setState(report.passed ? AppState.VALIDATION_COMPLETE : AppState.ERROR);
    } catch (e) {
      console.error(e);
      setState(AppState.ERROR);
    }
  };

  const startSimulation = async () => {
    if (!validationReport) return;
    setState(AppState.SIMULATING);
    try {
      const report = await api.runSimulation(validationReport.package_name, validationReport.node_name);
      setSimulationReport(report);
      setState(AppState.COMPLETE);
    } catch (e) {
      console.error(e);
      setState(AppState.ERROR);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8 text-white">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="border-b border-gray-700 pb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">ROS 2 Auto-Grader</h1>
            <p className="text-gray-400 mt-2">UR5e Gazebo Simulation & Code Validation Suite</p>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
            <span className="text-sm font-mono text-green-400">System: Ready</span>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Controls */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Upload Section */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <CloudArrowUpIcon className="h-6 w-6 mr-2 text-blue-400" />
                Submission
              </h2>
              <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${file ? 'border-green-500 bg-green-500/10' : 'border-gray-600 hover:border-blue-500 hover:bg-gray-700'}`}
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  className="hidden" 
                  accept=".zip"
                />
                {file ? (
                  <div className="text-green-400 font-medium">{file.name}</div>
                ) : (
                  <div className="text-gray-400">
                    <p>Click to upload .zip package</p>
                    <p className="text-xs mt-2 text-gray-500">Must contain package.xml</p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="mt-6 space-y-3">
                <button
                  onClick={startValidation}
                  disabled={!file || state === AppState.VALIDATING}
                  className={`w-full py-3 px-4 rounded-lg font-bold flex items-center justify-center transition-all ${
                    !file ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 
                    'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                  }`}
                >
                  {state === AppState.VALIDATING ? (
                    <span className="animate-pulse">Validating...</span>
                  ) : (
                    <>
                      <BeakerIcon className="h-5 w-5 mr-2" />
                      Run Code Check
                    </>
                  )}
                </button>

                <button
                  onClick={startSimulation}
                  disabled={state !== AppState.VALIDATION_COMPLETE && state !== AppState.COMPLETE}
                  className={`w-full py-3 px-4 rounded-lg font-bold flex items-center justify-center transition-all ${
                    (state !== AppState.VALIDATION_COMPLETE && state !== AppState.COMPLETE) ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 
                    'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/30'
                  }`}
                >
                  {state === AppState.SIMULATING ? (
                    <span className="animate-pulse">Simulating...</span>
                  ) : (
                    <>
                      <PlayIcon className="h-5 w-5 mr-2" />
                      Run Simulation
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Status Panel */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold mb-4 text-gray-300">Pipeline Status</h3>
              <div className="space-y-4">
                <StatusItem label="Upload" status={file ? 'success' : 'pending'} />
                <StatusItem label="Validation" status={validationReport ? (validationReport.passed ? 'success' : 'error') : 'pending'} />
                <StatusItem label="Simulation" status={simulationReport ? (simulationReport.success ? 'success' : 'error') : 'pending'} />
              </div>
            </div>
          </div>

          {/* Right Column: Reports & Output */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Validation Report */}
            {validationReport && (
              <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 animation-fade-in">
                <div className="bg-gray-750 border-b border-gray-700 p-4 flex justify-between items-center bg-gray-900/50">
                  <h3 className="text-lg font-semibold flex items-center">
                    <DocumentTextIcon className="h-5 w-5 mr-2 text-blue-400" />
                    Code Analysis Report
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${validationReport.passed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    Score: {validationReport.score}/100
                  </span>
                </div>
                <div className="p-6 grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Package Details</h4>
                    <ul className="space-y-2 text-sm">
                      <li className="flex justify-between"><span className="text-gray-500">Name:</span> <span className="font-mono text-gray-200">{validationReport.package_name}</span></li>
                      <li className="flex justify-between"><span className="text-gray-500">Node:</span> <span className="font-mono text-gray-200">{validationReport.node_name}</span></li>
                      <li className="flex justify-between"><span className="text-gray-500">Type:</span> <span className="text-gray-200">{validationReport.details.node_type}</span></li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Heuristics</h4>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-center">
                        {validationReport.details.has_package_xml ? <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2"/> : <XCircleIcon className="h-4 w-4 text-red-500 mr-2"/>}
                        package.xml detected
                      </li>
                      <li className="flex items-center">
                         {validationReport.details.has_build_file ? <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2"/> : <XCircleIcon className="h-4 w-4 text-red-500 mr-2"/>}
                        Build file detected
                      </li>
                    </ul>
                  </div>
                  
                  {validationReport.warnings.length > 0 && (
                     <div className="col-span-2 mt-2">
                       <h4 className="text-sm font-bold text-yellow-500 uppercase tracking-wider mb-2">Warnings</h4>
                       <div className="bg-yellow-500/10 border border-yellow-500/20 rounded p-3 text-sm text-yellow-200 font-mono">
                         {validationReport.warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
                       </div>
                     </div>
                  )}
                  
                  {validationReport.errors.length > 0 && (
                     <div className="col-span-2 mt-2">
                       <h4 className="text-sm font-bold text-red-500 uppercase tracking-wider mb-2">Critical Errors</h4>
                       <div className="bg-red-500/10 border border-red-500/20 rounded p-3 text-sm text-red-200 font-mono">
                         {validationReport.errors.map((e, i) => <div key={i}>✖ {e}</div>)}
                       </div>
                     </div>
                  )}
                </div>
              </div>
            )}

            {/* Simulation Results */}
            {simulationReport && (
              <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 animation-fade-in">
                <div className="bg-gray-750 border-b border-gray-700 p-4 flex justify-between items-center bg-gray-900/50">
                  <h3 className="text-lg font-semibold flex items-center">
                    <VideoCameraIcon className="h-5 w-5 mr-2 text-purple-400" />
                    Simulation Results
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${simulationReport.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {simulationReport.success ? 'PASSED' : 'FAILED'}
                  </span>
                </div>
                
                <div className="p-6">
                  {/* Visual Feedback */}
                  <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                     <div className="bg-black rounded-lg aspect-video flex items-center justify-center overflow-hidden border border-gray-600">
                        {simulationReport.screenshot_url ? (
                            <img src={simulationReport.screenshot_url} alt="Simulation Result" className="w-full h-full object-cover" />
                        ) : (
                            <span className="text-gray-500">No visual available</span>
                        )}
                     </div>
                     <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs overflow-y-auto h-full max-h-[250px] border border-gray-700">
                        <div className="text-gray-500 mb-2 border-b border-gray-700 pb-1">Simulation Logs /joint_states</div>
                        <pre className="text-green-400 whitespace-pre-wrap">{simulationReport.logs}</pre>
                     </div>
                  </div>

                  <div className="bg-gray-700/50 rounded p-4">
                    <h4 className="text-sm font-bold text-gray-300 mb-1">Outcome</h4>
                    <p className="text-white">{simulationReport.message}</p>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
};

const StatusItem: React.FC<{label: string, status: 'pending'|'success'|'error'}> = ({ label, status }) => {
  const colors = {
    pending: 'bg-gray-700 border-gray-600 text-gray-500',
    success: 'bg-green-500/10 border-green-500/50 text-green-400',
    error: 'bg-red-500/10 border-red-500/50 text-red-400'
  };

  return (
    <div className={`flex items-center justify-between p-3 rounded border ${colors[status]}`}>
      <span className="font-medium">{label}</span>
      {status === 'success' && <CheckCircleIcon className="h-5 w-5" />}
      {status === 'error' && <XCircleIcon className="h-5 w-5" />}
      {status === 'pending' && <div className="h-2 w-2 rounded-full bg-gray-500" />}
    </div>
  );
}

export default App;