import React, { useState, useEffect, useCallback } from 'react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
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
  const [treeData, setTreeData] = useState<any>(null);
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const [renamingItem, setRenamingItem] = useState<string | null>(null);
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
    const childItems: FileSystemItem[] = childIds.map((childId: string) => {
      const childNode = treeData.nodes[childId];
      return convertTreeNodeToFileSystemItem(childNode);
    });

    // Update the file list
    setItems(childItems);
    setCurrentPath(node.path_abs.replace(/\|/g, '/'));
    setCurrentNodeId(nodeId);
    setSelectedItems([]);
    
    console.log(`Loaded ${childItems.length} items from tree node:`, node.name);
  }, [treeData]);

  useEffect(() => {
    loadDirectory(currentPath);
  }, [currentPath]);

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
    
    // Check if this path exists in our tree data
    if (treeData) {
      // Find node by path
      const normalizedPath = path.replace(/\//g, '|');
      const nodeEntry = Object.entries(treeData.nodes).find(([_, node]: [string, any]) => 
        node.path_abs === normalizedPath
      );
      
      if (nodeEntry && (nodeEntry[1] as any).is_dir === 1) {
        // Load from tree data instead of file system
        loadFolderFromTree(nodeEntry[0]);
        return;
      }
    }
    
    // Fallback to original file system navigation
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

  const handleItemDoubleClick = useCallback((item: FileSystemItem) => {
    if (item.type === 'folder') {
      // Try to navigate using tree data first, then fallback to file system
      handleNavigate(item.path);
    } else {
      // Open file in system default application
      if ((window as any)?.clarity?.openInSystem) {
        (window as any).clarity.openInSystem(item.path);
      } else {
        console.log('Would open file:', item.path);
        toast({
          title: 'File Action',
          description: `Would open ${item.name} in system default application`
        });
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

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const results = await fileAPI.searchFiles(query);
      setSearchResults(results);
      setSearchQuery(query);
      setSelectedItems([]);
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

  const handleNewFolder = async () => {
    if (isSearching) {
      toast({
        title: 'Cannot Create Folder',
        description: 'Cannot create folders in search results',
        variant: 'destructive'
      });
      return;
    }

    const folderName = prompt('Enter folder name:');
    if (!folderName) return;

    try {
      const success = await fileAPI.createFolder(currentPath, folderName);
      if (success) {
        await loadDirectory(currentPath);
        toast({
          title: 'Success',
          description: `Folder "${folderName}" created successfully`
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

  const handleCopy = () => {
    if (selectedItems.length === 0) return;
    setClipboard({ items: selectedItems, operation: 'copy' });
    toast({
      title: 'Copied',
      description: `${selectedItems.length} item(s) copied to clipboard`
    });
  };

  const handleCut = () => {
    if (selectedItems.length === 0) return;
    setClipboard({ items: selectedItems, operation: 'cut' });
    toast({
      title: 'Cut',
      description: `${selectedItems.length} item(s) cut to clipboard`
    });
  };

  const handlePaste = async () => {
    if (!clipboard || isSearching) return;

    try {
      // In a real implementation, this would move/copy files
      console.log(`${clipboard.operation} operation:`, clipboard.items, 'to', currentPath);
      
      toast({
        title: 'Success',
        description: `${clipboard.items.length} item(s) ${clipboard.operation === 'copy' ? 'copied' : 'moved'}`
      });

      if (clipboard.operation === 'cut') {
        setClipboard(null);
      }
      
      await loadDirectory(currentPath);
    } catch (error) {
      console.error('Paste operation failed:', error);
      toast({
        title: 'Error',
        description: 'Paste operation failed',
        variant: 'destructive'
      });
    }
  };

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
      
      await loadDirectory(currentPath);
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

  // Keyboard shortcuts
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

      // Ctrl/Cmd shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'c':
            e.preventDefault();
            handleCopy();
            break;
          case 'x':
            e.preventDefault();
            handleCut();
            break;
          case 'v':
            e.preventDefault();
            handlePaste();
            break;
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
            canPaste={Boolean(clipboard)}
            onNewFolder={handleNewFolder}
            onCopy={handleCopy}
            onPaste={handlePaste}
            onCut={handleCut}
            onRename={() => {
              if (selectedItems.length === 1) {
                const item = displayItems.find(item => item.path === selectedItems[0]);
                if (item) handleStartRename(item);
              }
            }}
            onDelete={handleDelete}
            onRefresh={handleRefresh}
          />

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