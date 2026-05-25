```tsx
import React, { useState } from 'react';
import { Button, Input, Table, Tag } from 'antd';
import { PlayCircleOutlined, DownloadOutlined, SearchOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons';

// Mock Data
const mockChatMessages = [
  {
    id: '1',
    role: 'agent',
    content: '您好，我是客服小王，很高兴为您服务。请问有什么可以帮助您的吗？',
    timestamp: '09:30',
    wordCount: 28,
    duration: '00:05',
    isViolation: false,
    violationHighlight: []
  },
  {
    id: '2',
    role: 'customer',
    content: '我想咨询一下关于退款的问题',
    timestamp: '09:31',
    wordCount: 14,
    duration: '00:03',
    isViolation: false,
    violationHighlight: []
  },
  {
    id: '3',
    role: 'agent',
    content: '好的，您这个问题我不太清楚，您自己去看一下退款政策吧。',
    timestamp: '09:32',
    wordCount: 26,
    duration: '00:04',
    isViolation: true,
    violationHighlight: ['您自己去看一下']
  },
  {
    id: '4',
    role: 'customer',
    content: '可是我找不到相关信息啊',
    timestamp: '09:33',
    wordCount: 12,
    duration: '00:02',
    isViolation: false,
    violationHighlight: []
  },
  {
    id: '5',
    role: 'agent',
    content: '那我也没办法，这个不归我管。',
    timestamp: '09:34',
    wordCount: 14,
    duration: '00:03',
    isViolation: true,
    violationHighlight: ['那我也没办法', '这个不归我管']
  }
];

const mockQualityData = [
  { key: '1', taskName: '服务态度', inspector: '/', reviewer: '/', inspectionStatus: '/', score: null },
  { key: '2', taskName: '业务行为规范', inspector: '全检件', reviewer: '只检件', inspectionStatus: '/', score: -5 },
  { key: '3', taskName: '未及时回复', inspector: '全检件', reviewer: '全检件', inspectionStatus: '未命中', score: 0 },
  { key: '4', taskName: '用语规范', inspector: '全检件', reviewer: '全检件', inspectionStatus: '未命中', score: 0 },
  { key: '5', taskName: '服务禁忌', inspector: '全检件', reviewer: '全检件', inspectionStatus: '未命中', score: 0 },
  { key: '6', taskName: '业务知识', inspector: '全检件', reviewer: '全检件', inspectionStatus: '未命中', score: 0 }
];

const mockViolations = [
  { category: '条件A', ruleName: '类/行为规范', hitStatus: '命中', playbackLink: '#' },
  { category: '条件B', ruleName: '通用/文明用语', hitStatus: '未命中', playbackLink: null }
];

// Components
const Header: React.FC = () => {
  return (
    <div className="flex justify-between items-center py-3 mb-4">
      <div className="text-sm text-gray-700">
        流水号: S20260429235505047019OAF8CF4803622079
      </div>
      <div className="flex gap-2">
        <Button icon={<DownloadOutlined />}>文本下载</Button>
        <Button icon={<DownloadOutlined />}>立即下载</Button>
        <Button icon={<PlayCircleOutlined />}>录音试听</Button>
        <Button>回传记录查询</Button>
      </div>
    </div>
  );
};

const ChatToolbar: React.FC = () => {
  return (
    <div className="flex items-center gap-2 h-8 mb-3">
      <Button type="text" size="small">筛选文本</Button>
      <Tag color="green" className="cursor-pointer">开场白</Tag>
      <span className="text-xs text-gray-500">开场 0</span>
      <span className="text-xs text-gray-500">篇 0</span>
      <Button size="small" icon={<LeftOutlined />}>上一个</Button>
      <Button size="small" icon={<RightOutlined />}>下一个</Button>
      <Input
        size="small"
        placeholder="请输入关键词、序号、会话标识"
        prefix={<SearchOutlined />}
        className="w-64"
      />
    </div>
  );
};

interface ChatMessageProps {
  message: typeof mockChatMessages[0];
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isAgent = message.role === 'agent';
  
  const renderContent = () => {
    if (!message.isViolation) {
      return <span>{message.content}</span>;
    }
    
    let content = message.content;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    
    message.violationHighlight.forEach((highlight, idx) => {
      const index = content.indexOf(highlight, lastIndex);
      if (index !== -1) {
        if (index > lastIndex) {
          parts.push(<span key={`text-${idx}`}>{content.substring(lastIndex, index)}</span>);
        }
        parts.push(
          <span key={`highlight-${idx}`} className="text-red-500 font-medium">
            {highlight}
          </span>
        );
        lastIndex = index + highlight.length;
      }
    });
    
    if (lastIndex < content.length) {
      parts.push(<span key="text-end">{content.substring(lastIndex)}</span>);
    }
    
    return <>{parts}</>;
  };
  
  return (
    <div className={`flex gap-2 mb-4 ${isAgent ? '' : 'flex-row-reverse'}`}>
      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white text-sm ${
        isAgent ? 'bg-blue-500' : 'bg-green-500'
      }`}>
        {isAgent ? '客' : '户'}
      </div>
      <div className={`flex flex-col ${isAgent ? 'items-start' : 'items-end'} max-w-[70%]`}>
        <div className={`px-3 py-2 rounded-lg ${
          isAgent ? 'bg-gray-100' : 'bg-white border border-gray-200'
        }`}>
          {renderContent()}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-400">{message.wordCount}字</span>
          <span className="text-xs text-gray-400">{message.timestamp}</span>
          <PlayCircleOutlined className="text-xs text-blue-500 cursor-pointer" />
        </div>
      </div>
    </div>
  );
};

const ChatMessageList: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-2">
      {mockChatMessages.map(message => (
        <ChatMessage key={message.id} message={message} />
      ))}
    </div>
  );
};

const AudioWaveform: React.FC = () => {
  return (
    <div className="h-12 bg-gray-900 rounded mt-3 flex items-center px-4">
      <div className="flex-1 flex items-center gap-1">
        {Array.from({ length: 60 }).map((_, i) => (
          <div
            key={i}
            className="w-1 bg-cyan-400 rounded"
            style={{ height: `${Math.random() * 80 + 20}%` }}
          />
        ))}
      </div>
      <div className="ml-4 text-white text-xs">00:10 / 03:06</div>
    </div>
  );
};

const LeftPanel: React.FC = () => {
  return (
    <div className="flex-[3] flex flex-col bg-white rounded shadow-sm">
      <div className="p-3 border-b border-gray-200">
        <ChatToolbar />
      </div>
      <ChatMessageList />
      <div className="px-4 pb-3">
        <AudioWaveform />
      </div>
    </div>
  );
};

const QualityScoreTable: React.FC = () => {
  const columns = [
    {
      title: '质检任务',
      dataIndex: 'taskName',
      key: 'taskName',
      width: 'auto'
    },
    {
      title: '质检员',
      dataIndex: 'inspector',
      key: 'inspector',
      width: 80
    },
    {
      title: '复检员中',
      dataIndex: 'reviewer',
      key: 'reviewer',
      width: 80
    },
    {
      title: '质检备中',
      dataIndex: 'inspectionStatus',
      key: 'inspectionStatus',
      width: 80
    },
    {
      title: '评价',
      dataIndex: 'score',
      key: 'score',
      width: 60,
      render: (score: number | null) => {
        if (score === null) return '/';
        if (score < 0) return <span className="text-red-500">{score}</span>;
        return score;
      }
    }
  ];
  
  return (
    <Table
      columns={columns}
      dataSource={mockQualityData}
      pagination={false}
      size="small"
      className="mb-3"
    />
  );
};

const ViolationSection: React.FC = () => {
  const [expandedKeys, setExpandedKeys] = useState<string[]>(['0']);
  
  const toggleExpand = (key: string) => {
    setExpandedKeys(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };
  
  return (
    <div className="border-2 border-red-500 rounded p-3 mt-3">
      <div className="flex items-center gap-2 mb-2">
        <Tag color="red" className="m-0">违规点</Tag>
        <span className="text-sm text-red-500">检测到服务态度问题，请及时整改</span>
      </div>
      
      <div className="space-y-2">
        {mockViolations.map((violation, index) => (
          <div key={index} className="border border-gray-200 rounded">
            <div
              className="flex justify-between items-center p-2 cursor-pointer hover:bg-gray-50"
              onClick={() => toggleExpand(String(index))}
            >
              <span className="text-sm">
                {violation.category} {violation.ruleName}
              </span>
              <div className="flex items-center gap-2">
                {violation.hitStatus === '命中' && violation.playbackLink && (
                  <a href={violation.playbackLink} className="text-blue-500 text-xs">
                    回放对应（命中）
                  </a>
                )}
                {violation.hitStatus === '未命中' && (
                  <span className="text-gray-400 text-xs">未命中</span>
                )}
                <span className="text-gray-400">
                  {expandedKeys.includes(String(index)) ? '▼' : '▶'}
                </span>
              </div>
            </div>
            {expandedKeys.includes(String(index)) && (
              <div className="p-2 bg-gray-50 text-xs text-gray-600 border-t border-gray-200">
                违规详情：{violation.ruleName}相关内容
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const RightPanel: React.FC = () => {
  return (
    <div className="flex-[2] bg-white rounded shadow-sm p-3 flex flex-col">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-base font-semibold">成绩结果（质检成绩）</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">质检时:</span>
          <Button danger size="small">申诉</Button>
        </div>
      </div>
      
      <QualityScoreTable />
      <ViolationSection />
      
      <div className="mt-auto pt-3 border-t border-gray-200 flex justify-between items-center text-xs text-gray-500">
        <span>总量 50</span>
        <span>页码 1/1</span>
      </div>
    </div>
  );
};

const QualityInspectionPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-[1600px] mx-auto">
        <Header />
        <div className="flex gap-4">
          <LeftPanel />
          <RightPanel />
        </div>
      </div>
    </div>
  );
};

export default QualityInspectionPage;
```

这个实现包含了：

1. **完整的组件结构**：Header、LeftPanel（聊天区）、RightPanel（质检结果区）
2. **Tailwind CSS 样式**：所有样式都使用 Tailwind 类名
3. **Ant Design 组件**：Button、Input、Table、Tag
4. **模拟数据**：聊天消息、质检评分、违规详情
5. **交互功能**：
   - 违规文本高亮显示（红色）
   - 折叠面板展开/收起
   - 音频波形可视化
   - 响应式布局（flex 布局）
6. **中文界面**：所有文本都是中文
7. **组件化设计**：每个功能模块都是独立组件

代码可以直接在 React 项目中使用，需要安装依赖：
```bash
npm install antd @ant-design/icons
```