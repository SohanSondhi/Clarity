import React, { useState, useEffect, useCallback } from 'react';
import { FluentProvider, webLightTheme, Dialog, DialogSurface, DialogBody, DialogTitle, DialogActions, Button, Input } from '@fluentui/react-components';
import { CommandBar } from './CommandBar';
import { BreadcrumbBar } from './BreadcrumbBar';
import { FileList } from './FileList';
import { StatusBar } from './StatusBar';
import { TreeView } from './TreeView';
import { FileSystemItem, fileAPI, SearchResult } from '../lib/api';
import { useToast } from '../hooks/use-toast';

export const FileExplorer: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>('C:/Users/User');
  const [items, setItems] = useState<FileSystemItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [sortField, setSortField] = useState<keyof FileSystemItem>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [clipboard, setClipboard] = useState<{ items: string[], operation: 'copy' | 'cut' } | null>(null);
  const [loading, setLoading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexLogs, setIndexLogs] = useState<string[]>([]);
  const [treeData, setTreeData] = useState<any>(null);
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const [renamingItem, setRenamingItem] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const { toast } = useToast();

  const isSearching = Boolean(searchResults);
  const displayItems = isSearching ? searchResults!.items : items;

  // Convert tree node to FileSystemItem
  const convertTreeNodeToFileSystemItem = (node: any): FileSystemItem => {
    return {
      name: node.name,
      path: node.path_abs.replace(/\|/g, '/'), // Convert | back to / for display
      type: node.is_dir === 1 ? 'folder' : 'file',
      size: node.size_bytes || 0,
      dateModified: node.when_modified ? new Date(node.when_modified * 1000) : new Date(),
      extension: node.ext || undefined,
      description: `Tree item: ${node.name}`,
    };
  };

  // Load folder contents from tree data
  const loadFolderFromTree = useCallback((nodeId: string) => {
    if (!treeData) return;
    
    const node = treeData.nodes[nodeId];
    if (!node) return;

    // Get children from adjacency list (preserves order!)
    const childIds = treeData.adjacency_list[nodeId] || [];
    const childItems: FileSystemItem[] = childIds.map((childId: string) => convertTreeNodeToFileSystemItem(treeData.nodes[childId]));

    // Update the file list
    setItems(childItems);
    setCurrentPath(node.path_abs.replace(/\|/g, '/'));
    setCurrentNodeId(nodeId);
    setSelectedItems([]);
    
    console.log(`Loaded ${childItems.length} items from tree node:`, node.name);
  }, [treeData]);

  useEffect(() => {
    // Only fetch from filesystem when not viewing a tree node
    if (!currentNodeId) {
      loadDirectory(currentPath);
    }
  }, [currentPath, currentNodeId]);

  // Load tree data on startup
  useEffect(() => {
    const loadTreeData = async () => {
      try {
        // Fetch from your API endpoint instead of static file
        const response = await fetch('http://127.0.0.1:8001/tree');
        if (response.ok) {
          const data = await response.json();
          setTreeData(data);
          console.log('Tree data loaded:', data.metadata);
        }
      } catch (error) {
        console.warn('Could not load tree data:', error);
      }
    };
    loadTreeData();
  }, []);

  // Load root level when tree data is available
  useEffect(() => {
    if (treeData && treeData.root_ids && treeData.root_ids.length > 0) {
      loadFolderFromTree(treeData.root_ids[0]);
    }
  }, [treeData, loadFolderFromTree]);

  const loadDirectory = async (path: string) => {
    setLoading(true);
    try {
      const directoryItems = await fileAPI.getDirectoryContents(path);
      setItems(directoryItems);
      setSelectedItems([]);
    } catch (error) {
      console.error('Failed to load directory:', error);
      toast({
        title: 'Error',
        description: 'Failed to load directory contents',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = useCallback((path: string) => {
    if (isSearching) {
      setSearchResults(null);
      setSearchQuery('');
    }
    
    // Prefer tree data for deterministic ordering and contents
    if (treeData) {
      const normalizedPath = path.replace(/\//g, '|');
      const entry = Object.entries(treeData.nodes).find(([_, node]: [string, any]) => node.path_abs === normalizedPath);
      if (entry && (entry[1] as any).is_dir === 1) {
        loadFolderFromTree(entry[0]);
        return;
      }
    }
    // If not in tree, clear currentNodeId and fall back to FS list
    setCurrentNodeId(null);
    setCurrentPath(path);
  }, [isSearching, treeData, loadFolderFromTree]);

  const handleItemSelect = useCallback((path: string, isMultiSelect = false, isRangeSelect = false) => {
    setSelectedItems(prev => {
      if (isRangeSelect && prev.length > 0) {
        // Range selection logic
        const lastSelectedIndex = displayItems.findIndex(item => item.path === prev[prev.length - 1]);
        const currentIndex = displayItems.findIndex(item => item.path === path);
        
        if (lastSelectedIndex !== -1 && currentIndex !== -1) {
          const start = Math.min(lastSelectedIndex, currentIndex);
          const end = Math.max(lastSelectedIndex, currentIndex);
          const rangeItems = displayItems.slice(start, end + 1).map(item => item.path);
          return [...new Set([...prev, ...rangeItems])];
        }
      }
      
      if (isMultiSelect) {
        return prev.includes(path) 
          ? prev.filter(item => item !== path)
          : [...prev, path];
      } else {
        return prev.includes(path) && prev.length === 1 ? [] : [path];
      }
    });
  }, [displayItems]);

  const handleItemDoubleClick = useCallback(async (item: FileSystemItem) => {
    if (item.type === 'folder') {
      // Try to navigate using tree data first, then fallback to file system
      handleNavigate(item.path);
    } else {
      // Open file in system default application via Electron IPC
      const fullPath = item.path.replace(/\//g, '\\');
      const api = (window as any)?.api;
      if (api?.openPath) {
        const res = await api.openPath(fullPath);
        if (!res?.success) {
          toast({ title: 'Open failed', description: res?.error || 'Unknown error', variant: 'destructive' });
        }
      } else {
        toast({ title: 'Unavailable', description: 'Desktop bridge not available. Restart the app.', variant: 'destructive' });
      }
    }
  }, [handleNavigate, toast]);

  const handleSort = useCallback((field: keyof FileSystemItem) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField]);

  const handleSearch = async (query: string, searchType: 'text' | 'image' = 'text') => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const results = await fileAPI.searchFiles(query, searchType);
      setSearchResults(results);
      setSearchQuery(query);
      setSelectedItems([]);
      
      // If we got results, show a success message and open the first result
      if (results.items.length > 0) {
        const firstResult = results.items[0];
        toast({
          title: 'Search Complete',
          description: `Found ${results.totalResults} result(s). Opening: ${firstResult.name}`,
        });
        
        // Open the file using the system default application
        // This will work on Windows, Mac, and Linux
        if (window.clarity && window.clarity.openInSystem) {
          window.clarity.openInSystem(firstResult.path);
        } else if (window.electronAPI && window.electronAPI.openFile) {
          window.electronAPI.openFile(firstResult.path);
        } else {
          // Fallback: try to open with a web link (for web browsers)
          console.log('File found:', firstResult.path);
          // You could also show the file in a dialog or navigate to its location
        }
      } else {
        toast({
          title: 'No Results',
          description: `No ${searchType} results found for "${query}"`,
        });
      }
    } catch (error) {
      console.error('Search failed:', error);
      toast({
        title: 'Search Error',
        description: 'Failed to perform search',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClearSearch = () => {
    setSearchResults(null);
    setSearchQuery('');
    setSelectedItems([]);
  };

  const handleNewFolder = () => {
    if (isSearching) {
      toast({
        title: 'Cannot Create Folder',
        description: 'Cannot create folders in search results',
        variant: 'destructive'
      });
      return;
    }
    setNewFolderName('');
    setIsCreateDialogOpen(true);
  };

  const submitCreateFolder = async () => {
    const folderName = newFolderName.trim();
    if (!folderName) return;

    try {
      // Close immediately for instant UX
      setIsCreateDialogOpen(false);
      setNewFolderName('');

      const success = await fileAPI.createFolder(currentPath, folderName);
      if (success) {
        try {
          const resp = await fetch('http://127.0.0.1:8001/refresh', { method: 'POST' });
          if (resp.ok) {
            const newTree = await resp.json();
            setTreeData(newTree);
          }
        } catch {}

        if (currentNodeId && treeData) {
          loadFolderFromTree(currentNodeId);
        } else {
          await loadDirectory(currentPath);
        }

        toast({
          title: 'Success',
          description: `Folder "${folderName}" created successfully`
        });
      } else {
        toast({
          title: 'Error',
          description: 'Failed to create folder',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Failed to create folder:', error);
      toast({
        title: 'Error',
        description: 'Failed to create folder',
        variant: 'destructive'
      });
    }
  };

  // Copy removed

  const handleCut = () => {
    if (selectedItems.length === 0) return;
    setClipboard({ items: selectedItems, operation: 'cut' });
    toast({
      title: 'Cut',
      description: `${selectedItems.length} item(s) cut to clipboard`
    });
  };

  // Paste removed

  const handleStartRename = (item: FileSystemItem) => {
    // Start inline rename mode
    setRenamingItem(item.path);
  };

  const handleRename = async (oldPath: string, newName: string) => {
    if (!newName.trim()) {
      setRenamingItem(null);
      return;
    }

    try {
      // Guard: Only allow rename when the item exists in the indexed tree
      if (treeData) {
        const normalized = oldPath.replace(/\//g, '|');
        const nodeEntry = Object.entries(treeData.nodes).find(([_id, node]: [string, any]) => node.path_abs === normalized);
        if (!nodeEntry) {
          toast({
            title: 'Not indexed',
            description: 'This item is not in the indexed tree. Navigate using the File Tree and try again.',
            variant: 'destructive'
          });
          setRenamingItem(null);
          return;
        }
      }

      setLoading(true);
      const success = await fileAPI.renameItem(oldPath, newName);
      
      if (success) {
        // Ask backend to rebuild and return the latest tree
        try {
          const resp = await fetch('http://127.0.0.1:8001/refresh', { method: 'POST' });
          if (resp.ok) {
            const newTree = await resp.json();
            setTreeData(newTree);
          }
        } catch {}

        // Refresh the current view
        if (currentNodeId && treeData) {
          loadFolderFromTree(currentNodeId);
        } else {
          await loadDirectory(currentPath);
        }

        const oldName = oldPath.split('/').pop() || oldPath;
        toast({
          title: 'Success',
          description: `Renamed "${oldName}" to "${newName}"`
        });
      } else {
        throw new Error('Rename operation returned false');
      }
    } catch (error) {
      console.error('Rename failed:', error);
      const oldName = oldPath.split('/').pop() || oldPath;
      toast({
        title: 'Error',
        description: `Failed to rename "${oldName}". Please try again.`,
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRenamingItem(null); // Clear renaming state
    }
  };

  const handleDelete = async () => {
    if (selectedItems.length === 0) return;

    const confirmed = confirm(`Move ${selectedItems.length} item(s) to Recycle Bin?`);
    if (!confirmed) return;

    try {
      for (const itemPath of selectedItems) {
        await fileAPI.deleteItem(itemPath);
      }

      // Rebuild and reload the tree so the left panel updates too
      try {
        const resp = await fetch('http://127.0.0.1:8001/refresh', { method: 'POST' });
        if (resp.ok) {
          const newTree = await resp.json();
          setTreeData(newTree);
        }
      } catch {}

      if (currentNodeId && treeData) {
        loadFolderFromTree(currentNodeId);
      } else {
        await loadDirectory(currentPath);
      }
      setSelectedItems([]);
      
      toast({
        title: 'Success',
        description: `${selectedItems.length} item(s) moved to Recycle Bin`
      });
    } catch (error) {
      console.error('Delete failed:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete items',
        variant: 'destructive'
      });
    }
  };

  const handleRefresh = () => {
    const doRefresh = async () => {
      try {
        const resp = await fetch('http://127.0.0.1:8001/refresh', { method: 'POST' });
        if (resp.ok) {
          const newTree = await resp.json();
          setTreeData(newTree);
        }
      } catch {}

      if (isSearching) {
        handleSearch(searchQuery);
      } else if (currentNodeId && treeData) {
        loadFolderFromTree(currentNodeId);
      } else {
        loadDirectory(currentPath);
      }
    };
    doRefresh();
  };

  const handleRunIndex = async (rootDir: string) => {
    const dir = rootDir.trim();
    if (!dir) return;
    setLoading(true);
    setIsIndexing(true);
    setIndexLogs([]);
    try {
      // Use passed-in directory; do not rely on env defaults
      const newTree = await fileAPI.runIndex(dir);
      setTreeData(newTree);
      if (Array.isArray(newTree?.index_logs)) {
        setIndexLogs(newTree.index_logs);
      }
      // Load first root after reindex
      if (newTree?.root_ids?.length) {
        loadFolderFromTree(newTree.root_ids[0]);
      }
      toast({ title: 'Index complete', description: `Indexed: ${dir}` });
    } catch (e: any) {
      toast({ title: 'Index failed', description: e?.message || 'Unknown error', variant: 'destructive' });
    } finally {
      setLoading(false);
      setIsIndexing(false);
    }
  };

  const handleClearAll = async () => {
    setLoading(true);
    try {
      await fileAPI.clearAll();
      // Clear UI state
      setTreeData(null);
      setCurrentNodeId(null);
      setItems([]);
      toast({ title: 'Cleared', description: 'Database and tree file removed' });
    } catch (e: any) {
      toast({ title: 'Clear failed', description: e?.message || 'Unknown error', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  // Keyboard shortcuts (copy/paste removed)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;

      switch (e.key) {
        case 'F5':
          e.preventDefault();
          handleRefresh();
          break;
        case 'Delete':
          if (selectedItems.length > 0) {
            handleDelete();
          }
          break;
        case 'F2':
          if (selectedItems.length === 1) {
            const item = displayItems.find(item => item.path === selectedItems[0]);
            if (item) {
              handleStartRename(item);
            }
          }
          break;
        case 'Backspace':
          if (!isSearching && currentPath !== 'C:/') {
            const parentPath = currentPath.split('/').slice(0, -1).join('/') || 'C:/';
            handleNavigate(parentPath);
          }
          break;
        case 'Enter':
          if (selectedItems.length === 1) {
            const item = displayItems.find(item => item.path === selectedItems[0]);
            if (item) {
              handleItemDoubleClick(item);
            }
          }
          break;
      }

      // Ctrl/Cmd shortcuts (copy/paste removed)
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          // no-op
          case 'a':
            e.preventDefault();
            setSelectedItems(displayItems.map(item => item.path));
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPath, selectedItems, displayItems, isSearching, searchQuery, clipboard]);

  return (
    <FluentProvider theme={webLightTheme}>
      <div className="flex h-screen bg-background text-foreground">
        {/* Indexing overlay */}
        {isIndexing && (
          <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center">
            <div className="bg-white rounded shadow-lg p-4 w-[520px] max-h-[70vh] flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin border-2 border-gray-300 border-t-blue-600 rounded-full" />
                  <span className="font-medium">Indexing in progress…</span>
                </div>
              </div>
              <div className="text-xs text-gray-600 border rounded p-2 bg-gray-50 overflow-auto" style={{ minHeight: 180 }}>
                {indexLogs.length === 0 ? (
                  <div>Starting…</div>
                ) : (
                  indexLogs.map((l, i) => (
                    <div key={i} className="whitespace-pre-wrap break-all">{l}</div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
        {/* TreeView Panel */}
        <div className="w-80 border-r border-gray-200 bg-white">
          <TreeView 
            data={treeData}
            onNodeSelect={(node) => {
              console.log('Selected node:', node.name);
              // For folders, load contents immediately on single click
              if (node.is_dir === 1) {
                loadFolderFromTree(node.id);
              }
            }}
            onNodeDoubleClick={(node) => {
              // Double-click behavior: load folder contents (same as single click for now)
              if (node.is_dir === 1) {
                loadFolderFromTree(node.id);
              } else {
                // For files, you could add "open file" functionality here
                console.log('Double-clicked file:', node.name);
              }
            }}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Command Bar */}
          <CommandBar
            selectedItems={selectedItems}
            onNewFolder={handleNewFolder}
            onRename={() => {
              if (selectedItems.length === 1) {
                const item = displayItems.find(item => item.path === selectedItems[0]);
                if (item) handleStartRename(item);
              }
            }}
            onDelete={handleDelete}
            onRefresh={handleRefresh}
            onRunIndex={handleRunIndex}
            onClearAll={handleClearAll}
          />

          {/* Create Folder Dialog */}
          <Dialog open={isCreateDialogOpen} onOpenChange={(_e, data) => setIsCreateDialogOpen(!!data.open)}>
            <DialogSurface>
              <DialogBody>
                <DialogTitle>Create new folder</DialogTitle>
                <div className="p-2">
                  <Input
                    placeholder="Folder name"
                    value={newFolderName}
                    onChange={(e) => setNewFolderName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') submitCreateFolder();
                    }}
                    autoFocus
                  />
                </div>
                <DialogActions>
                  <Button appearance="secondary" onClick={() => { setIsCreateDialogOpen(false); setNewFolderName(''); }}>Cancel</Button>
                  <Button appearance="primary" onClick={submitCreateFolder}>Create</Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>

          {/* Breadcrumb and Search */}
          <BreadcrumbBar
            currentPath={currentPath}
            searchQuery={searchQuery}
            isSearching={isSearching}
            onNavigate={handleNavigate}
            onSearch={handleSearch}
            onClearSearch={handleClearSearch}
          />

          {/* File List */}
          <FileList
            items={displayItems}
            selectedItems={selectedItems}
            sortField={sortField}
            sortDirection={sortDirection}
            onItemSelect={handleItemSelect}
            onItemDoubleClick={handleItemDoubleClick}
            onSort={handleSort}
            onRename={handleRename}
            renamingItem={renamingItem || undefined}
            onStartRename={(path) => setRenamingItem(path)}
          />

          {/* Status Bar */}
          <StatusBar
            totalItems={displayItems.length}
            selectedItems={selectedItems}
            allItems={displayItems}
          />
        </div>
      </div>
    </FluentProvider>
  );
};