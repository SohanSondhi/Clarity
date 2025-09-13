import React, { useState, useEffect, useCallback } from 'react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { Sidebar } from './Sidebar';
import { CommandBar } from './CommandBar';
import { BreadcrumbBar } from './BreadcrumbBar';
import { FileList } from './FileList';
import { StatusBar } from './StatusBar';
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
  const { toast } = useToast();

  const isSearching = Boolean(searchResults);
  const displayItems = isSearching ? searchResults!.items : items;

  useEffect(() => {
    loadDirectory(currentPath);
  }, [currentPath]);

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
    setCurrentPath(path);
  }, [isSearching]);

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

  const handleRename = async (item: FileSystemItem) => {
    try {
      const success = await fileAPI.renameItem(item.path, item.name);
      if (success) {
        await loadDirectory(currentPath);
        toast({
          title: 'Success',
          description: `Item renamed successfully`
        });
      }
    } catch (error) {
      console.error('Rename failed:', error);
      toast({
        title: 'Error',
        description: 'Failed to rename item',
        variant: 'destructive'
      });
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
    if (isSearching) {
      handleSearch(searchQuery);
    } else {
      loadDirectory(currentPath);
    }
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
              handleRename(item);
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
        {/* Sidebar */}
        <Sidebar 
          currentPath={currentPath}
          onNavigate={handleNavigate}
        />

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
                if (item) handleRename(item);
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