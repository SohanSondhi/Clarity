// Type definitions for Electron preload bridge
declare global {
  interface Window {
    clarity?: {
      openInSystem: (path: string) => void;
    };
    electronAPI?: {
      openFile: (path: string) => void;
    };
  }
}

export {};