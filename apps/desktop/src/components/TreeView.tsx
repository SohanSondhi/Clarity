import React, { useState, useEffect } from 'react';
import {
  ChevronRight24Regular,
  ChevronDown24Regular,
  Folder24Regular,
  Document24Regular,
  Image24Regular,
  MusicNote224Regular,
  Video24Regular,
  Archive24Regular,
  Apps24Regular,
} from '@fluentui/react-icons';

// Types matching your tree.py output
interface TreeNode {
  id: string;
  path_abs: string;
  parent_id: string | null;
  name: string;
  is_dir: 0 | 1;
  ext: string;
  size_bytes: number | null;
  when_created: number | null;
  when_modified: number | null;
  is_synthetic: boolean;
}

interface TreeData {
  nodes: Record<string, TreeNode>;
  adjacency_list: Record<string, string[]>;
  root_ids: string[];
  metadata: {
    total_nodes: number;
    total_files: number;
    total_directories: number;
    synthetic_directories: number;
  };
}

interface TreeViewProps {
  onNodeSelect?: (node: TreeNode) => void;
  onNodeDoubleClick?: (node: TreeNode) => void;
  data?: TreeData | null; // Controlled tree data from parent (optional)
}

export const TreeView: React.FC<TreeViewProps> = ({ 
  onNodeSelect, 
  onNodeDoubleClick,
  data
}) => {
  const [treeData, setTreeData] = useState<TreeData | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load tree data
  useEffect(() => {
    // If parent provides data, use it and skip fetching
    if (data) {
      setTreeData(data);
      setExpandedNodes(new Set(data.root_ids));
      setLoading(false);
      return;
    }

    const loadTreeData = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/tree');
        if (!response.ok) {
          throw new Error(`Failed to load tree data: ${response.status} - ${response.statusText}`);
        }
        const remote: TreeData = await response.json();
        setTreeData(remote);
        setExpandedNodes(new Set(remote.root_ids));
      } catch (err) {
        console.error('Error loading tree data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadTreeData();
  }, [data]);

  // Get file icon based on extension
  const getFileIcon = (node: TreeNode) => {
    if (node.is_dir === 1) {
      return <Folder24Regular className="w-4 h-4 text-blue-600" />;
    }
    
    const ext = node.ext?.toLowerCase();
    switch (ext) {
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
        return <Image24Regular className="w-4 h-4 text-green-600" />;
      case 'mp3':
      case 'wav':
      case 'flac':
        return <MusicNote224Regular className="w-4 h-4 text-purple-600" />;
      case 'mp4':
      case 'avi':
      case 'mkv':
        return <Video24Regular className="w-4 h-4 text-red-600" />;
      case 'zip':
      case 'rar':
      case '7z':
        return <Archive24Regular className="w-4 h-4 text-orange-600" />;
      case 'exe':
      case 'msi':
        return <Apps24Regular className="w-4 h-4 text-gray-600" />;
      default:
        return <Document24Regular className="w-4 h-4 text-gray-600" />;
    }
  };

  // Toggle node expansion
  const toggleExpanded = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (expandedNodes.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Handle node selection
  const handleNodeClick = (node: TreeNode) => {
    setSelectedNode(node.id);
    onNodeSelect?.(node);
  };

  // Handle node double-click
  const handleNodeDoubleClick = (node: TreeNode) => {
    if (node.is_dir === 1) {
      toggleExpanded(node.id);
    }
    onNodeDoubleClick?.(node);
  };

  // Render a single tree node
  const renderNode = (nodeId: string, level: number = 0): React.ReactNode => {
    const node = treeData!.nodes[nodeId];
    if (!node) return null;

    const isDirectory = node.is_dir === 1;
    const isExpanded = expandedNodes.has(nodeId);
    const isSelected = selectedNode === nodeId;
    const hasChildren = treeData!.adjacency_list[nodeId]?.length > 0;

    // Get children in order from adjacency list
    const childIds = treeData!.adjacency_list[nodeId] || [];

    return (
      <div key={nodeId}>
        {/* Node itself */}
        <div
          className={`flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 ${
            isSelected ? 'bg-blue-100 text-blue-800' : ''
          }`}
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => handleNodeClick(node)}
          onDoubleClick={() => handleNodeDoubleClick(node)}
        >
          {/* Expand/collapse icon */}
          <div className="w-4 h-4 mr-1 flex items-center justify-center">
            {isDirectory && hasChildren ? (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpanded(nodeId);
                }}
                className="p-0 border-none bg-transparent cursor-pointer hover:bg-gray-200 rounded"
              >
                {isExpanded ? (
                  <ChevronDown24Regular className="w-3 h-3" />
                ) : (
                  <ChevronRight24Regular className="w-3 h-3" />
                )}
              </button>
            ) : null}
          </div>

          {/* File/folder icon */}
          <div className="mr-2">
            {getFileIcon(node)}
          </div>

          {/* Node name */}
          <span className="text-sm truncate flex-1" title={node.path_abs}>
            {node.name}
          </span>
        </div>

        {/* Children (if expanded) */}
        {isDirectory && isExpanded && hasChildren && (
          <div>
            {childIds.map(childId => renderNode(childId, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        Loading tree structure...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        Error: {error}
      </div>
    );
  }

  if (!treeData) {
    return (
      <div className="p-4 text-center text-gray-500">
        No tree data available
      </div>
    );
  }

  return (
    <div className="tree-view h-full overflow-auto bg-white">
      {/* Header */}
      <div className="p-3 border-b bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700">File Tree</h3>
        <p className="text-xs text-gray-500">
          {treeData.metadata.total_files} files, {treeData.metadata.total_directories} folders
        </p>
      </div>

      {/* Tree content */}
      <div className="p-2">
        {treeData.root_ids.map(rootId => renderNode(rootId, 0))}
      </div>
    </div>
  );
};

export default TreeView;
