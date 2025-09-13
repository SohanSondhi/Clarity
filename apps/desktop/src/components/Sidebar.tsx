import React, { useState, useEffect } from 'react';
import {
  Tree,
  TreeItem,
  TreeItemLayout,
  Button,
} from '@fluentui/react-components';
import {
  Folder24Regular,
  FolderOpen24Regular,
  HardDrive24Regular,
  Star24Regular,
  ChevronRight24Regular,
  ChevronDown24Regular,
} from '@fluentui/react-icons';
import { fileAPI, QuickAccessItem, DriveInfo, FileSystemItem } from '../lib/api';

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

interface TreeNode {
  id: string;
  name: string;
  path: string;
  type: 'quick-access' | 'drive' | 'folder';
  icon: React.ReactNode;
  children?: TreeNode[];
  expanded?: boolean;
  loading?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPath, onNavigate }) => {
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [quickAccess, drives] = await Promise.all([
        fileAPI.getQuickAccessItems(),
        fileAPI.getDrives()
      ]);

      const quickAccessNode: TreeNode = {
        id: 'quick-access',
        name: 'Quick access',
        path: '',
        type: 'quick-access',
        icon: <Star24Regular />,
        children: quickAccess.map((item: QuickAccessItem) => ({
          id: `qa-${item.path}`,
          name: item.name,
          path: item.path,
          type: 'folder' as const,
          icon: <Folder24Regular />
        })),
        expanded: true
      };

      const driveNodes: TreeNode[] = drives.map((drive: DriveInfo) => ({
        id: `drive-${drive.path}`,
        name: drive.name,
        path: drive.path,
        type: 'drive',
        icon: <HardDrive24Regular />,
        children: [],
        expanded: false
      }));

      setTreeData([quickAccessNode, ...driveNodes]);
      setExpandedItems(new Set(['quick-access']));
    } catch (error) {
      console.error('Failed to load sidebar data:', error);
    }
  };

  const loadFolderContents = async (node: TreeNode) => {
    if (node.type === 'quick-access') return;

    try {
      const items = await fileAPI.getDirectoryContents(node.path);
      const folderItems = items
        .filter(item => item.type === 'folder')
        .map(item => ({
          id: `folder-${item.path}`,
          name: item.name,
          path: item.path,
          type: 'folder' as const,
          icon: <Folder24Regular />,
          children: [],
          expanded: false
        }));

      setTreeData(prevData => 
        updateTreeNode(prevData, node.id, { 
          ...node, 
          children: folderItems,
          loading: false 
        })
      );
    } catch (error) {
      console.error('Failed to load folder contents:', error);
    }
  };

  const updateTreeNode = (nodes: TreeNode[], nodeId: string, updates: Partial<TreeNode>): TreeNode[] => {
    return nodes.map(node => {
      if (node.id === nodeId) {
        return { ...node, ...updates };
      }
      if (node.children) {
        return { ...node, children: updateTreeNode(node.children, nodeId, updates) };
      }
      return node;
    });
  };

  const handleToggleExpansion = (nodeId: string, node: TreeNode) => {
    const isExpanded = expandedItems.has(nodeId);
    
    if (!isExpanded) {
      setExpandedItems(prev => new Set([...prev, nodeId]));
      
      // Load children if not loaded yet
      if (node.type !== 'quick-access' && (!node.children || node.children.length === 0)) {
        setTreeData(prevData => 
          updateTreeNode(prevData, nodeId, { ...node, loading: true })
        );
        loadFolderContents(node);
      }
    } else {
      setExpandedItems(prev => {
        const next = new Set(prev);
        next.delete(nodeId);
        return next;
      });
    }
  };

  const handleNodeClick = (node: TreeNode) => {
    if (node.type !== 'quick-access' && node.path) {
      onNavigate(node.path);
    }
  };

  const renderTreeNode = (node: TreeNode): React.ReactNode => {
    const isExpanded = expandedItems.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = node.path === currentPath;

    return (
      <TreeItem
        key={node.id}
        itemType={hasChildren || node.type === 'quick-access' ? 'branch' : 'leaf'}
        value={node.id}
      >
        <TreeItemLayout
          iconBefore={
            hasChildren || node.type === 'quick-access' ? (
              <Button
                appearance="subtle"
                size="small"
                icon={isExpanded ? <ChevronDown24Regular /> : <ChevronRight24Regular />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleExpansion(node.id, node);
                }}
                className="w-6 h-6 min-w-6"
              />
            ) : (
              <div className="w-6" />
            )
          }
          aside={<div className="flex items-center">{node.icon}</div>}
          className={`px-2 py-1 text-sm cursor-pointer rounded transition-colors ${
            isSelected 
              ? 'bg-explorer-sidebar-selected text-primary' 
              : 'hover:bg-explorer-sidebar-hover'
          }`}
          onClick={() => handleNodeClick(node)}
        >
          {node.name}
          {node.loading && <span className="ml-2 text-xs text-muted-foreground">Loading...</span>}
        </TreeItemLayout>
        {isExpanded && hasChildren && (
          <Tree>
            {node.children!.map(child => renderTreeNode(child))}
          </Tree>
        )}
      </TreeItem>
    );
  };

  return (
    <div className="w-64 h-full bg-explorer-sidebar border-r border-border">
      <div className="p-3">
        <Tree>
          {treeData.map(node => renderTreeNode(node))}
        </Tree>
      </div>
    </div>
  );
};