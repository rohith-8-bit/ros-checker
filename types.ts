export interface ValidatorReport {
  passed: boolean;
  score: number;
  errors: string[];
  warnings: string[];
  package_name: string;
  node_name: string;
  details: {
    has_package_xml: boolean;
    has_build_file: boolean;
    node_type: 'ROS 1' | 'ROS 2' | 'Unknown';
    publishers: string[];
    subscribers: string[];
  };
}

export interface SimulationReport {
  success: boolean;
  message: string;
  video_url?: string;
  screenshot_url?: string;
  logs: string;
}

export enum AppState {
  IDLE = 'IDLE',
  VALIDATING = 'VALIDATING',
  VALIDATION_COMPLETE = 'VALIDATION_COMPLETE',
  SIMULATING = 'SIMULATING',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR'
}