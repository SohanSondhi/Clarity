import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import {
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Button,
  Checkbox,
} from '@fluentui/react-components';
import {
  Folder24Regular,
  Document24Regular,
  Image24Regular,
  MusicNote224Regular,
  Video24Regular,
  Archive24Regular,
  Apps24Regular,
  ChevronUp24Regular,
  ChevronDown24Regular,
} from '@fluentui/react-icons';
import { FileSystemItem, fileAPI } from '../lib/api';

interface FileListProps {
  items: FileSystemItem[];
  selectedItems: string[];
  sortField: keyof FileSystemItem;
  sortDirection: 'asc' | 'desc';
  onItemSelect: (path: string, isMultiSelect?: boolean, isRangeSelect?: boolean) => void;
  onItemDoubleClick: (item: FileSystemItem) => void;
  onSort: (field: keyof FileSystemItem) => void;
  onRename: (item: FileSystemItem) => void;
}

type SortableField = 'name' | 'dateModified' | 'type' | 'size';

const getFileIcon = (item: FileSystemItem) => {
  if (item.type === 'folder') {
    return <Folder24Regular className="w-5 h-5 text-blue-600" />;
  }
  
  const ext = item.extension?.toLowerCase();
  switch (ext) {
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'bmp':
      return <Image24Regular className="w-5 h-5 text-green-600" />;
    case 'mp3':
    case 'wav':
    case 'flac':
      return <MusicNote224Regular className="w-5 h-5 text-purple-600" />;
    case 'mp4':
    case 'avi':
    case 'mkv':
      return <Video24Regular className="w-5 h-5 text-red-600" />;
    case 'zip':
    case 'rar':
    case '7z':
      return <Archive24Regular className="w-5 h-5 text-orange-600" />;
    case 'exe':
    case 'msi':
      return <Apps24Regular className="w-5 h-5 text-gray-600" />;
    default:
      return <Document24Regular className="w-5 h-5 text-gray-600" />;
  }
};

interface ItemRowProps {
  index: number;
  style: React.CSSProperties;
  data: {
    items: FileSystemItem[];
    selectedItems: string[];
    onItemSelect: (path: string, isMultiSelect?: boolean, isRangeSelect?: boolean) => void;
    onItemDoubleClick: (item: FileSystemItem) => void;
    onRename: (item: FileSystemItem) => void;
  };
}

const ItemRow: React.FC<ItemRowProps> = ({ index, style, data }) => {
  const { items, selectedItems, onItemSelect, onItemDoubleClick, onRename } = data;
  const item = items[index];
  const isSelected = selectedItems.includes(item.path);
  const [renaming, setRenaming] = useState(false);
  const [renameName, setRenameName] = useState(item.name);

  const handleClick = (e: React.MouseEvent) => {
    const isCtrl = e.ctrlKey || e.metaKey;
    const isShift = e.shiftKey;
    onItemSelect(item.path, isCtrl, isShift);
  };

  const handleDoubleClick = () => {
    onItemDoubleClick(item);
  };

  const handleRename = () => {
    setRenaming(true);
    setRenameName(item.name);
  };

  const handleRenameSubmit = () => {
    if (renameName !== item.name) {
      onRename({ ...item, name: renameName });
    }
    setRenaming(false);
  };

  const handleRenameCancel = () => {
    setRenaming(false);
    setRenameName(item.name);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      handleRenameCancel();
    }
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  };

  const getFileType = (item: FileSystemItem) => {
    if (item.type === 'folder') return 'File folder';
    if (item.extension) {
      return fileAPI.getFileTypeFromExtension(item.extension);
    }
    return 'File';
  };

  return (
    <div
      style={style}
      className={`flex items-center px-3 py-1 border-b border-explorer-grid cursor-pointer hover:bg-explorer-item-hover ${
        isSelected ? 'bg-explorer-item-selected' : ''
      }`}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onContextMenu={(e) => {
        e.preventDefault();
        // TODO: Show context menu
      }}
    >
      <div className="w-6 flex justify-center mr-3">
        <Checkbox
          checked={isSelected}
          onChange={() => onItemSelect(item.path)}
        />
      </div>
      
      <div className="flex items-center min-w-0 flex-1">
        <div className="mr-2 flex-shrink-0">
          {getFileIcon(item)}
        </div>
        <div className="min-w-0 flex-1 mr-6">
          {renaming ? (
            <input
              type="text"
              value={renameName}
              onChange={(e) => setRenameName(e.target.value)}
              onBlur={handleRenameSubmit}
              onKeyDown={handleKeyDown}
              className="w-full px-1 py-0 text-sm border border-primary rounded focus:outline-none focus:ring-1 focus:ring-primary"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span className="text-sm truncate block">{item.name}</span>
          )}
        </div>
      </div>
      
      <div className="w-40 text-sm text-muted-foreground mr-6">
        {formatDate(item.dateModified)}
      </div>
      
      <div className="w-32 text-sm text-muted-foreground mr-6">
        {getFileType(item)}
      </div>
      
      <div className="w-20 text-sm text-muted-foreground text-right">
        {item.type === 'folder' ? '' : fileAPI.formatFileSize(item.size)}
      </div>
    </div>
  );
};

export const FileList: React.FC<FileListProps> = ({
  items,
  selectedItems,
  sortField,
  sortDirection,
  onItemSelect,
  onItemDoubleClick,
  onSort,
  onRename
}) => {
  const [listHeight, setListHeight] = useState(400);

  useEffect(() => {
    const updateHeight = () => {
      const availableHeight = window.innerHeight - 250; // Account for header, breadcrumb, status bar
      setListHeight(Math.max(200, availableHeight));
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);

  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      // Always put folders first
      if (a.type === 'folder' && b.type !== 'folder') return -1;
      if (a.type !== 'folder' && b.type === 'folder') return 1;

      let aValue: any = a[sortField as SortableField];
      let bValue: any = b[sortField as SortableField];

      if (sortField === 'dateModified') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      } else if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [items, sortField, sortDirection]);

  const handleSort = (field: SortableField) => {
    onSort(field);
  };

  const getSortIcon = (field: SortableField) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? 
      <ChevronUp24Regular className="w-3 h-3 ml-1" /> : 
      <ChevronDown24Regular className="w-3 h-3 ml-1" />;
  };

  const itemData = {
    items: sortedItems,
    selectedItems,
    onItemSelect,
    onItemDoubleClick,
    onRename
  };

  return (
    <div className="flex-1 bg-background">
      {/* Header */}
      <div className="flex items-center px-3 py-2 border-b border-explorer-grid bg-explorer-header text-sm font-medium">
        <div className="w-6 mr-3">
          <Checkbox
            checked={selectedItems.length === items.length && items.length > 0}
            onChange={() => {
              if (selectedItems.length === items.length) {
                // Deselect all
                selectedItems.forEach(path => onItemSelect(path, false, false));
              } else {
                // Select all
                items.forEach(item => {
                  if (!selectedItems.includes(item.path)) {
                    onItemSelect(item.path, true, false);
                  }
                });
              }
            }}
          />
        </div>
        
        <div className="flex items-center min-w-0 flex-1">
          <Button
            appearance="subtle"
            onClick={() => handleSort('name')}
            className="text-sm font-medium p-0 mr-6 justify-start"
          >
            Name {getSortIcon('name')}
          </Button>
        </div>
        
        <Button
          appearance="subtle"
          onClick={() => handleSort('dateModified')}
          className="w-40 text-sm font-medium p-0 mr-6 justify-start"
        >
          Date modified {getSortIcon('dateModified')}
        </Button>
        
        <Button
          appearance="subtle"
          onClick={() => handleSort('type')}
          className="w-32 text-sm font-medium p-0 mr-6 justify-start"
        >
          Type {getSortIcon('type')}
        </Button>
        
        <Button
          appearance="subtle"
          onClick={() => handleSort('size')}
          className="w-20 text-sm font-medium p-0 justify-end"
        >
          Size {getSortIcon('size')}
        </Button>
      </div>

      {/* List */}
      <List
        height={listHeight}
        width="100%"
        itemCount={sortedItems.length}
        itemSize={32}
        itemData={itemData}
        className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
      >
        {ItemRow}
      </List>
    </div>
  );
};