// API helper for file explorer operations
// Communicates with FastAPI backend at http://127.0.0.1:8765

export interface FileSystemItem {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size: number;
  dateModified: Date;
  description?: string;
  tags?: string[];
  extension?: string;
  icon?: string;
}

export interface QuickAccessItem {
  name: string;
  path: string;
  icon: string;
}

export interface DriveInfo {
  name: string;
  path: string;
  label: string;
  totalSpace: number;
  freeSpace: number;
  type: string;
}

export interface SearchResult {
  query: string;
  items: FileSystemItem[];
  totalResults: number;
}

// Add search type enum
export type SearchType = 'text' | 'image';

class FileExplorerAPI {
  private baseUrl = 'http://127.0.0.1:8001';

  // Mock data for development
  private mockFiles: FileSystemItem[] = [
    {
      name: 'Documents',
      path: 'C:/Users/User/Documents',
      type: 'folder',
      size: 0,
      dateModified: new Date('2024-01-15'),
      icon: '📁'
    },
    {
      name: 'Downloads',
      path: 'C:/Users/User/Downloads',
      type: 'folder',
      size: 0,
      dateModified: new Date('2024-01-20'),
      icon: '📁'
    },
    {
      name: 'Pictures',
      path: 'C:/Users/User/Pictures',
      type: 'folder',
      size: 0,
      dateModified: new Date('2024-01-18'),
      icon: '📁'
    },
    {
      name: 'Desktop',
      path: 'C:/Users/User/Desktop',
      type: 'folder',
      size: 0,
      dateModified: new Date('2024-01-22'),
      icon: '📁'
    },
    {
      name: 'report.docx',
      path: 'C:/Users/User/Documents/report.docx',
      type: 'file',
      size: 2048576,
      dateModified: new Date('2024-01-21'),
      extension: 'docx',
      icon: '📄'
    },
    {
      name: 'presentation.pptx',
      path: 'C:/Users/User/Documents/presentation.pptx',
      type: 'file',
      size: 5242880,
      dateModified: new Date('2024-01-19'),
      extension: 'pptx',
      icon: '📊'
    },
    {
      name: 'image.jpg',
      path: 'C:/Users/User/Pictures/image.jpg',
      type: 'file',
      size: 1048576,
      dateModified: new Date('2024-01-17'),
      extension: 'jpg',
      icon: '🖼️'
    }
  ];

  private mockQuickAccess: QuickAccessItem[] = [
    { name: 'Desktop', path: 'C:/Users/User/Desktop', icon: '🖥️' },
    { name: 'Downloads', path: 'C:/Users/User/Downloads', icon: '⬇️' },
    { name: 'Documents', path: 'C:/Users/User/Documents', icon: '📁' },
    { name: 'Pictures', path: 'C:/Users/User/Pictures', icon: '🖼️' }
  ];

  private mockDrives: DriveInfo[] = [
    {
      name: 'Local Disk (C:)',
      path: 'C:/',
      label: 'Windows',
      totalSpace: 500000000000,
      freeSpace: 250000000000,
      type: 'NTFS'
    },
    {
      name: 'Data (D:)',
      path: 'D:/',
      label: 'Data',
      totalSpace: 1000000000000,
      freeSpace: 800000000000,
      type: 'NTFS'
    }
  ];

  async getDirectoryContents(path: string): Promise<FileSystemItem[]> {
    // Right pane mirrors the indexed tree; we don't call a backend directory API.
    // Return empty here; the component populates from tree data when available.
    return [];
  }

  async searchFiles(query: string, searchType: SearchType = 'text'): Promise<SearchResult> {
    try {
      let endpoint = '/search-text';
      let body: any = { query };

      if (searchType === 'image') {
        endpoint = '/search-image';
        body = { query: query };
      }

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Convert API response to SearchResult format
              return {
                query: result.query,
        items: result.results.map((item: any) => ({
          name: item.path.split('/').pop() || item.path.split('\\').pop() || item.path,
          path: item.path,
          type: 'file' as const,
          size: 0,
          dateModified: new Date(),
          extension: item.path.split('.').pop() || '',
          description: `${searchType} search result`,
        })),
        totalResults: result.total_results
      };
    } catch (error) {
      console.warn('Search API not available, using mock data:', error);
      // Return mock search results
      const filteredItems = this.mockFiles.filter(item =>
        item.name.toLowerCase().includes(query.toLowerCase())
      );
      
      return {
        query,
        items: filteredItems,
        totalResults: filteredItems.length
      };
    }
  }

  async getQuickAccessItems(): Promise<QuickAccessItem[]> {
    // Not used yet – return empty to avoid calling backend
    return [];
  }

  async getDrives(): Promise<DriveInfo[]> {
    // Not used yet – return empty to avoid calling backend
    return [];
  }

  async createFolder(path: string, name: string): Promise<boolean> {
    try {
      // Convert parent path to '|' delimiter format for backend
      const parent_path = path.replace(/\//g, '|');
      const response = await fetch(`${this.baseUrl}/create-folder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ parent_path, name }),
      });
      return response.ok;
    } catch (error) {
      console.error('Create folder API error:', error);
      return false;
    }
  }

  async deleteItem(path: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path }),
      });
      
      return response.ok;
    } catch (error) {
      console.warn('Delete API not available, simulating success:', error);
      return true;
    }
  }

  async runIndex(rootDir: string, options?: { dbPath?: string; tableName?: string; outputPath?: string }): Promise<any> {
    const body: any = { root_dir: rootDir };
    if (options?.dbPath) body.db_path = options.dbPath;
    if (options?.tableName) body.table_name = options.tableName;
    if (options?.outputPath) body.output_path = options.outputPath;
    const response = await fetch(`${this.baseUrl}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const msg = await response.text();
      throw new Error(`Index failed: ${response.status} ${msg}`);
    }
    return response.json();
  }

  async clearAll(options?: { dbPath?: string; outputPath?: string }): Promise<boolean> {
    const body: any = {};
    if (options?.dbPath) body.db_path = options.dbPath;
    if (options?.outputPath) body.output_path = options.outputPath;
    const response = await fetch(`${this.baseUrl}/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const msg = await response.text();
      throw new Error(`Clear failed: ${response.status} ${msg}`);
    }
    return true;
  }


  async renameItem(oldPath: string, newName: string): Promise<boolean> {
    try {
      // Convert path from frontend format (/) to API format (|)
      const normalizedPath = oldPath.replace(/\//g, '|');
      
      const response = await fetch(`${this.baseUrl}/rename`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          old_path: normalizedPath, 
          new_name: newName 
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Rename successful:', result);
        return true;
      } else {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Rename failed:', error);
        return false;
      }
    } catch (error) {
      console.warn('Rename API not available, simulating success:', error);
      return true;
    }
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getFileTypeFromExtension(extension: string): string {
    const types: { [key: string]: string } = {
      'pdf': 'PDF Document',
      'docx': 'Microsoft Word Document',
      'xlsx': 'Microsoft Excel Spreadsheet',
      'pptx': 'Microsoft PowerPoint Presentation',
      'txt': 'Text Document',
      'jpg': 'JPEG Image',
      'jpeg': 'JPEG Image',
      'png': 'PNG Image',
      'gif': 'GIF Image',
      'mp4': 'MP4 Video',
      'avi': 'AVI Video',
      'mp3': 'MP3 Audio',
      'wav': 'WAV Audio',
      'zip': 'ZIP Archive',
      'exe': 'Application'
    };
    return types[extension.toLowerCase()] || `${extension.toUpperCase()} File`;
  }
}

export const fileAPI = new FileExplorerAPI();