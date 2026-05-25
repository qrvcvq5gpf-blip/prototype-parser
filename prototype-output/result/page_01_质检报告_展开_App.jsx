

```tsx
import React, { useState, useRef, useEffect } from "react";
import { Table, Button, Tabs, Tag, Tooltip, Modal, Badge } from "antd";
import {
  DownloadOutlined,
  StarOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SoundOutlined,
  CloseOutlined,
  ExclamationCircleOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  InfoCircleOutlined,
  UserOutlined,
  CustomerServiceOutlined,
  ExpandOutlined,
} from "@ant-design/icons";

// ==================== Mock Data ====================

const mockReportData = {
  reportId: "2026043400B4800/J",
  batchNumber: "S2026042920504485850B0A4FCE4800177061",
  detectType: "智能质检",
  detectTime: "2026-04-30 14:23:00",
  detectResult: "合格",
  score: 92,
  agentName: "李晓燕",
  agentId: "A10086",
  customerId: "C20240001",
};

const mockDialogData = [
  {
    dialogId: "1",
    speaker: "客服",
    speakerId: "A10086",
    speakerName: "李晓燕",
    content: "您好，中国石化客户服务中心，工号10086，很高兴为您服务，请问有什么可以帮到您？",
    timestamp: "00:00:03",
    duration: 5.2,
    qualityIssues: [],
  },
  {
    dialogId: "2",
    speaker: "客户",
    speakerId: "C20240001",
    speakerName: "客户",
    content: "你好，我想问一下我上次在你们加油站办的那个加油卡，现在余额怎么查不到了？",
    timestamp: "00:00:09",
    duration: 4.8,
    qualityIssues: [],
  },
  {
    dialogId: "3",
    speaker: "客服",
    speakerId: "A10086",
    speakerName: "李晓燕",
    content: "好的，请您稍等，我帮您查询一下。请问您能提供一下您的加油卡号码或者办卡时预留的手机号码吗？",
    timestamp: "00:00:15",
    duration: 6.1,
    qualityIssues: [],
  },
  {
    dialogId: "4",
    speaker: "客户",
    speakerId: "C20240001",
    speakerName: "客户",
    content: "手机号是138****5678，卡号我不太记得了。",
    timestamp: "00:00:22",
    duration: 3.5,
    qualityIssues: [],
  },
  {
    dialogId: "5",
    speaker: "客服",
    speakerId: "A10086",
    speakerName: "李晓燕",
    content: "好的，已经帮您查到了。您的加油卡号是6200****8899，当前卡内余额为356.50元。您说查不到余额，是在哪个渠道查询的呢？",
    timestamp: "00:00:27",
    duration: 8.3,
    qualityIssues: [],
  },
  {
    dialogId: "6",
    speaker: "客户",
    speakerId: "C20240001",
    speakerName: "客户",
    content: "我在你们那个APP上面查的，一直显示网络错误。",
    timestamp: "00:00:36",
    duration: 3.2,
    qualityIssues: [],
  },
  {
    dialogId: "7",
    speaker: "客服",
    speakerId: "A10086",
    speakerName: "李晓燕",
    content:
      "非常抱歉给您带来不便。可能是近期系统升级导致的，建议您可以尝试清除APP缓存后重新登录，或者更新到最新版本试试看。如果还是不行的话，您也可以通过微信公众号"中国石化"来查询余额。",
    timestamp: "00:00:40",
    duration: 12.5,
    qualityIssues: [
      {
        issueType: "服务规范",
        description: "未主动提供工单记录",
        severity: "low" as const,
      },
    ],
  },
  {
    dialogId: "8",
    speaker: "客户",
    speakerId: "C20240001",
    speakerName: "客户",
    content: "好的，那我试试看。另外我还想问下，你们最近有什么充值优惠活动吗？",
    timestamp: "00:00:54",
    duration: 4.1,
    qualityIssues: [],
  },
  {
    dialogId: "9",
    speaker: "客服",
    speakerId: "A10086",
    speakerName: "李晓燕",
    content:
      "有的呢！目前我们正在进行五一劳动节充值优惠活动，充500元赠30元，充1000元赠80元，活动截止到5月5日。您可以在各网点或者APP上参与充值活动。",
    timestamp: "00:00:59",
    duration: 10.2,
    qualityIssues: [],
  },
  {
    dialogId: "10",
    speaker: "客户",
    speakerId: "C20240001",
    speakerName: "客户",
    content: "好的，谢谢你。那没其他问题了。",
    timestamp: "00:01:10",
    duration: 2.8,
    qualityIssues: [],
  },
  {
    dialogId: "11",
    speaker: "客服",
    speakerId: "A10086",
    speakerName: "李晓燕",
    content: "不客气，感谢您的来电。如果后续还有其他问题，欢迎随时拨打我们的客服热线。祝您生活愉快，再见！",
    timestamp: "00:01:14",
    duration: 7.1,
    qualityIssues: [],
  },
];

const mockQualityItems = [
  { key: "1", itemName: "开头语规范", result: "已通过", score: 10, detail: "符合标准开头语要求" },
  { key: "2", itemName: "服务态度", result: "已通过", score: 15, detail: "语气亲切，态度良好" },
  { key: "3", itemName: "业务解答准确性", result: "已通过", score: 20, detail: "业务信息准确无误" },
  { key: "4", itemName: "问题解决能力", result: "已通过", score: 15, detail: "有效解决客户问题" },
  {
    key: "5",
    itemName: "主动服务意识",
    result: "未通过",
    score: 8,
    detail: "未主动提供工单跟踪服务",
  },
  { key: "6", itemName: "结束语规范", result: "已通过", score: 10, detail: "符合标准结束语要求" },
  { key: "7", itemName: "通话时长合规", result: "已通过", score: 14, detail: "通话时长在合理范围内" },
];

// ==================== Sub Components ====================

// 通知横幅组件
const NotificationBanner: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  return (
    <div className="flex items-center justify-between bg-blue-50 border-b border-blue-100 px-6 py-2.5">
      <div className="flex items-center gap-2">
        <InfoCircleOutlined className="text-blue-500" />
        <span className="text-sm text-gray-600">
          欢迎使用中石化智能质检系统！系统已升级至V3.2版本，新增AI评价报告功能。
        </span>
      </div>
      <div className="flex items-center gap-3">
        <Button type="link" size="small" className="text-blue-600 p-0">
          查看更新日志
        </Button>
        <CloseOutlined
          className="text-gray-400 hover:text-gray-600 cursor-pointer text-xs"
          onClick={onClose}
        />
      </div>
    </div>
  );
};

// 标题栏组件
const HeaderBar: React.FC = () => {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-1 h-5 bg-blue-600 rounded-full flex-shrink-0" />
        <h1 className="text-base font-semibold text-gray-800 truncate">
          高级质检报告
          <span className="text-gray-400 font-normal ml-2 text-sm">
            编号: {mockReportData.reportId}
          </span>
        </h1>
        <Tag color="blue" className="flex-shrink-0 text-xs">
          批次号: {mockReportData.batchNumber.slice(0, 20)}...
        </Tag>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <Button size="small" icon={<StarOutlined />}>
          质量等级
        </Button>
        <Button size="small" icon={<FileTextOutlined />}>
          工单打卡
        </Button>
        <Button size="small" icon={<DownloadOutlined />}>
          数据下载
        </Button>
        <Button size="small" icon={<ExclamationCircleOutlined />}>
          评分回收
        </Button>
      </div>
    </div>
  );
};

// 对话气泡组件
const DialogBubble: React.FC<{
  item: (typeof mockDialogData)[0];
  onClickIssue?: () => void;
}> = ({ item, onClickIssue }) => {
  const isAgent = item.speaker === "客服";
  const hasIssues = item.qualityIssues && item.qualityIssues.length > 0;

  return (
    <div className={`flex gap-3 ${isAgent ? "" : "flex-row-reverse"}`}>
      {/* 头像 */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs ${
          isAgent ? "bg-blue-500" : "bg-green-500"
        }`}
      >
        {isAgent ? <CustomerServiceOutlined /> : <UserOutlined />}
      </div>

      {/* 消息体 */}
      <div className={`max-w-[70%] ${isAgent ? "" : "text-right"}`}>
        {/* 名称和时间 */}
        <div
          className={`flex items-center gap-2 mb-1 text-xs text-gray-400 ${
            isAgent ? "" : "justify-end"
          }`}
        >
          <span className="font-medium text-gray-500">{item.speakerName}</span>
          <span>{item.timestamp}</span>
          <span className="text-gray-300">({item.duration}s)</span>
        </div>

        {/* 气泡 */}
        <div
          className={`inline-block rounded-lg px-4 py-3 text-sm leading-relaxed relative ${
            isAgent
              ? "bg-gray-50 text-gray-700 rounded-tl-sm"
              : "bg-blue-50 text-gray-700 rounded-tr-sm"
          } ${hasIssues ? "border-2 border-red-200" : ""}`}
        >
          {item.content}
          {hasIssues && (
            <div className="mt-2 pt-2 border-t border-red-100">
              {item.qualityIssues.map((issue, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-1.5 cursor-pointer hover:bg-red-50 rounded px-1 py-0.5 -mx-1"
                  onClick={onClickIssue}
                >
                  <ExclamationCircleOutlined className="text-red-400 text-xs" />
                  <span className="text-xs text-red-500">
                    {issue.issueType}: {issue.description}
                  </span>
                  <Tag
                    color={
                      issue.severity === "high"
                        ? "red"
                        : issue.severity === "medium"
                        ? "orange"
                        : "gold"
                    }
                    className="text-xs ml-1 px-1"
                    style={{ fontSize: 10 }}
                  >
                    {issue.severity === "high"
                      ? "高"
                      : issue.severity === "medium"
                      ? "中"
                      : "低"}
                  </Tag>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// 对话列表组件
const DialogList: React.FC<{ onClickIssue: () => void }> = ({ onClickIssue }) => {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* 通话信息摘要 */}
      <div className="flex items-center justify-center">
        <div className="bg-gray-100 text-gray-400 text-xs px-4 py-1 rounded-full">
          通话开始 · 2026-04-30 14:23:00 · 总时长 01:21
        </div>
      </div>

      {mockDialogData.map((item) => (
        <DialogBubble key={item.dialogId} item={item} onClickIssue={onClickIssue} />
      ))}

      {/* 通话结束 */}
      <div className="flex items-center justify-center">
        <div className="bg-gray-100 text-gray-400 text-xs px-4 py-1 rounded-full">
          通话结束 · 客户挂断
        </div>
      </div>
    </div>
  );
};

// 质检结果面板组件
const QualityResultPanel: React.FC = () => {
  const columns = [
    {
      title: "质检项目",
      dataIndex: "itemName",
      key: "itemName",
      render: (text: string) => <span className="text-sm text-gray-700">{text}</span>,
    },
    {
      title: "检测结果",
      dataIndex: "result",
      key: "result",
      width: 100,
      render: (text: string) => (
        <span className="flex items-center gap-1">
          {text === "已通过" ? (
            <CheckCircleFilled className="text-green-500 text-xs" />
          ) : (
            <CloseCircleFilled className="text-red-500 text-xs" />
          )}
          <span className={`text-xs ${text === "已通过" ? "text-green-600" : "text-red-500"}`}>
            {text}
          </span>
        </span>
      ),
    },
    {
      title: "得分",
      dataIndex: "score",
      key: "score",
      width: 60,
      render: (score: number) => <span className="text-sm font-medium text-gray-700">{score}</span>,
    },
    {
      title: "详情",
      key: "action",
      width: 60,
      render: () => (
        <Button type="link" size="small" className="p-0 text-xs">
          查看
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* 质检结果概览 */}
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">质检结果</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">检测类型</div>
            <div className="text-sm font-medium text-gray-700">{mockReportData.detectType}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">检测时间</div>
            <div className="text-sm font-medium text-gray-700">
              {mockReportData.detectTime.split(" ")[0]}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">检测结果</div>
            <div className="flex items-center gap-1.5">
              <Badge status="success" />
              <span className="text-sm font-medium text-green-600">
                {mockReportData.detectResult}
              </span>
            </div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">综合得分</div>
            <div className="text-xl font-bold text-blue-600">
              {mockReportData.score}
              <span className="text-xs font-normal text-gray-400 ml-1">/ 100</span>
            </div>
          </div>
        </div>
      </div>

      {/* 坐席信息 */}
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-800 mb-2">坐席信息</h3>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center text-white">
            <CustomerServiceOutlined />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-700">{mockReportData.agentName}</div>
            <div className="text-xs text-gray-400">工号: {mockReportData.agentId}</div>
          </div>
        </div>
      </div>

      {/* 质检项列表 */}
      <div className="px-4 py-3 flex-1 overflow-y-auto">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">质检项目</h3>
        <Table
          columns={columns}
          dataSource={mockQualityItems}
          size="small"
          pagination={false}
          className="quality-table"
          rowClassName={(record) =>
            record.result === "未通过" ? "bg-red-50" : ""
          }
        />
      </div>

      {/* 批注区域 - 空状态 */}
      <div className="px-4 py-6 border-t border-gray-100">
        <div className="flex flex-col items-center text-gray-300">
          <FileTextOutlined className="text-3xl mb-2" />
          <span className="text-xs">暂无批注</span>
        </div>
      </div>
    </div>
  );
};

// 音频波形组件
const AudioWaveform: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const totalDuration = 81; // seconds
  const animRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    drawWaveform(ctx, rect.width, rect.height, currentTime / totalDuration);
  }, [currentTime]);

  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= totalDuration) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 0.1;
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isPlaying]);

  const drawWaveform = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    progress: number
  ) => {
    ctx.clearRect(0, 0, width, height);

    const barWidth = 2;
    const barGap = 1;
    const barCount = Math.floor(width / (barWidth + barGap));
    const centerY = height / 2;

    for (let i = 0; i < barCount; i++) {
      const x = i * (barWidth + barGap);
      const normalizedPos = i / barCount;

      // Generate pseudo-random waveform heights
      const seed = Math.sin(i * 0.15) * 0.5 + Math.sin(i * 0.08) * 0.3 + Math.sin(i * 0.25) * 0.2;
      const barHeight = Math.abs(seed) * (height * 0.7) + height * 0.05;

      const isPlayed = normalizedPos <= progress;
      ctx.fillStyle = isPlayed ? "#3B82F6" : "#D1D5DB";

      ctx.fillRect(x, centerY - barHeight / 2, barWidth, barHeight);
    }

    // Draw playhead
    const playheadX = progress * width;
    ctx.strokeStyle = "#2563EB";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(playheadX, 0);
    ctx.lineTo(playheadX, height);
    ctx.stroke();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const progress = x / rect.width;
    setCurrentTime(progress * totalDuration);
  };

  return (
    <div className="border-t border-gray-100 bg-gray-50 px-6 py-3">
      <div className="flex items-center gap-4">
        {/* 播放控制 */}
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-700 flex items-center justify-center text-white flex-shrink-0 transition-colors"
        >
          {isPlaying ? (
            <PauseCircleOutlined className="text-sm" />
          ) : (
            <PlayCircleOutlined className="text-sm" />
          )}
        </button>

        {/* 时间显示 */}
        <span className="text-xs text-gray-500 font-mono w-12 flex-shrink-0">
          {formatTime(currentTime)}
        </span>

        {/* 波形 */}
        <div className="flex-1 h-12 cursor-pointer">
          <canvas
            ref={canvasRef}
            className="w-full h-full"
            onClick={handleCanvasClick}
          />
        </div>

        {/* 总时长 */}
        <span className="text-xs text-gray-500 font-mono w-12 flex-shrink-0">
          {formatTime(totalDuration)}
        </span>

        {/* 音量 */}
        <SoundOutlined className="text-gray-400 text-sm" />
      </div>
    </div>
  );
};

// 弹窗组件
const IssueDetailModal: React.FC<{ visible: boolean; onClose: () => void }> = ({
  visible,
  onClose,
}) => {
  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <ExclamationCircleOutlined className="text-orange-500" />
          <span>质检问题详情</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={520}
      footer={[
        <Button key="compare" type="default">
          对比AI评价结果
        </Button>,
        <Button key="confirm" type="primary" onClick={onClose}>
          确定
        </Button>,
      ]}
    >
      <div className="py-2">
        <div className="bg-orange-50 border border-orange-100 rounded-lg p-4 mb-4">
          <div className="text-sm font-medium text-gray-800 mb-2">主动服务意识 - 未通过</div>
          <div className="text-sm text-gray-600">
            在第7句对话中，客服人员针对客户反馈的APP查询余额失败问题，仅提供了替代查询方案，
            但未主动为客户创建工单进行问题追踪和后续跟进。
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="text-xs text-gray-400 mb-1">相关对话</div>
            <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 border border-gray-100">
              "非常抱歉给您带来不便。可能是近期系统升级导致的，建议您可以尝试清除APP缓存后重新登录..."
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">扣分原因</div>
            <div className="text-sm text-gray-700">
              根据《客服质检标准V3.1》第5.2.3条规定，当客户反馈系统类故障时，客服人员应主动为客户创建故障工单，
              并告知工单编号及预计处理时间。本通话中客服未执行此操作，扣除"主动服务意识"项7分。
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">建议改进</div>
            <div className="text-sm text-green-700 bg-green-50 border border-green-100 rounded-lg p-3">
              建议在提供替代方案后，补充说明："我这边已经帮您记录了这个问题，工单编号为XXX，
              我们的技术团队会尽快处理，预计24小时内恢复正常，届时会有短信通知您。"
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

// ==================== Main Component ====================

const QualityInspectionReport: React.FC = () => {
  const [showBanner, setShowBanner] = useState(true);
  const [activeTab, setActiveTab] = useState("dialog");
  const [modalVisible, setModalVisible] = useState(false);

  const tabItems = [
    { key: "dialog", label: "对话文本" },
    { key: "quality", label: "质检项" },
    { key: "card1", label: "卡一卡" },
    { key: "card2", label: "卡二卡" },
    { key: "manual", label: "评论人工评价" },
    { key: "other", label: "其他" },
    {
      key: "ai",
      label: (
        <span className="flex items-center gap-1">
          AI评价报告
          <Badge count="新" size="small" className="ml-1" style={{ backgroundColor: "#3B82F6" }} />
        </span>
      ),
    },
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* 通知横幅 */}
      {showBanner && <NotificationBanner onClose={() => setShowBanner(false)} />}

      {/* 主体内容 */}
      <div className="flex-1 p-4 overflow-hidden">
        <div className="h-full bg-white rounded-lg shadow-sm flex flex-col overflow-hidden">
          {/* 标题栏 */}
          <HeaderBar />

          {/* 标签页 */}
          <div className="px-6 border-b border-gray-100">
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabItems}
              size="small"
              className="mb-0"
            />
          </div>

          {/* 内容区域 */}
          <div className="flex-1 flex overflow-hidden">
            {/* 左侧 - 对话区域 */}
            <div className="flex-1 flex flex-col border-r border-gray-100 min-w-0">
              {/* 搜索/筛选栏 */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-50 bg-gray-50/50">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">共 {mockDialogData.length} 条对话</span>
                  <span className="text-xs text-gray-300">|</span>
                  <span className="text-xs text-red-400">
                    1 个质检问题
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="small" type="text" className="text-xs text-gray-400">
                    仅看问题
                  </Button>
                  <Button size="small" type="text" icon={<ExpandOutlined />} className="text-xs text-gray-400">
                    展开
                  </Button>
                </div>
              </div>

              {/* 对话列表 */}
              <DialogList onClickIssue={() => setModalVisible(true)} />

              {/* 音频波形 */}
              <AudioWaveform />
            </div>

            {/* 右侧 - 详情面板 */}
            <div className="w-[380px] xl:w-[420px] flex-shrink-0 overflow-y-auto">
              <QualityResultPanel />
            </div>
          </div>
        </div>
      </div>

      {/* 问题详情弹窗 */}
      <IssueDetailModal visible={modalVisible} onClose={() => setModalVisible(false)} />
    </div>
  );
};

export default QualityInspectionReport;
```