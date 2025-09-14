import React from 'react';
import { 
  Button, 
  Toolbar, 
  ToolbarButton,
  Tooltip 
} from '@fluentui/react-components';
import {
  FolderAdd24Regular,
  Rename24Regular,
  Delete24Regular,
  ArrowSync24Regular,
  Share24Regular,
  MoreVertical24Regular
} from '@fluentui/react-icons';

interface CommandBarProps {
  selectedItems: string[];
  onNewFolder: () => void;
  onRename: () => void;
  onDelete: () => void;
  onRefresh: () => void;
  onShare?: () => void;
}

export const CommandBar: React.FC<CommandBarProps> = ({
  selectedItems,
  onNewFolder,
  onRename,
  onDelete,
  onRefresh,
  onShare
}) => {
  const hasSelection = selectedItems.length > 0;
  const hasMultipleSelection = selectedItems.length > 1;

  return (
    <div className="bg-explorer-header border-b border-border px-3 py-2">
      <Toolbar>
        <ToolbarButton
          appearance="subtle"
          icon={<FolderAdd24Regular />}
          onClick={onNewFolder}
        >
          New folder
        </ToolbarButton>
        
        <div className="w-px h-6 bg-border mx-2" />
                
        <div className="w-px h-6 bg-border mx-2" />
        
        <Tooltip content="Rename selected item" relationship="label">
          <ToolbarButton
            appearance="subtle"
            icon={<Rename24Regular />}
            disabled={!hasSelection || hasMultipleSelection}
            onClick={onRename}
          >
            Rename
          </ToolbarButton>
        </Tooltip>
        
        <Tooltip content="Move selected items to Recycle Bin" relationship="label">
          <ToolbarButton
            appearance="subtle"
            icon={<Delete24Regular />}
            disabled={!hasSelection}
            onClick={onDelete}
          >
            Delete
          </ToolbarButton>
        </Tooltip>
        
        <div className="w-px h-6 bg-border mx-2" />
        
        <Tooltip content="Refresh current folder" relationship="label">
          <ToolbarButton
            appearance="subtle"
            icon={<ArrowSync24Regular />}
            onClick={onRefresh}
          >
            Refresh
          </ToolbarButton>
        </Tooltip>
        
        {onShare && (
          <>
            <div className="w-px h-6 bg-border mx-2" />
            <Tooltip content="Share selected items" relationship="label">
              <ToolbarButton
                appearance="subtle"
                icon={<Share24Regular />}
                disabled={!hasSelection}
                onClick={onShare}
              >
                Share
              </ToolbarButton>
            </Tooltip>
          </>
        )}
        
        <div className="flex-1" />
        
        <ToolbarButton
          appearance="subtle"
          icon={<MoreVertical24Regular />}
        >
          More
        </ToolbarButton>
      </Toolbar>
    </div>
  );
};