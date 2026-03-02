---
description: 智能 MD-PDF 验证与修复流水线 - 处理原始 Mathpix Markdown 数据与源 PDF 文件，通过多专家 Agent 协作进行校验、修复。
---

# 智能 MD-PDF 验证与修复流水线 (ADRP - Antigravity Dual-Tier Refinement Protocol)

该工作流旨在处理原始 Mathpix Markdown 数据与源 PDF 文件，通过多专家 Agent 协作进行校验、修复，最终输出高置信度的 Markdown 结果。

## 1. Init & Config (初始化与配置)

1.  **加载配置**: 读取 `pipeline_config.json` 获取 API 密钥、模型选择及阈值设置。
2.  **设置环境**: 加载 `.env` 环境变量。

## 2. Inputs (输入层)

定义工作流的起始输入变量：

*   `raw_md`: **Mathpix MD (Raw)** - 原始的 Markdown 文本数据。
*   `source_pdf`: **源 PDF 文件** - 原始的 PDF 文档路径。
*   `chunk_size`: 文本分块大小 (默认 1500字符)。

## 3. Preprocessing (预处理层)

### 3.1 页面/分块拆分
使用 Python 脚本将 `raw_md` 拆分为逻辑块 (Chunks)，并建立与 PDF 页面的映射关系。

### 3.2 批处理初始化
计算总 Chunks 数量，初始化进度追踪器。

## 4. Main Processing Loop (主处理循环)

对于每个 Chunk，执行以下步骤：

### 4.1 Orchestrator Layer (协调层)
**协调 Agent (Orchestrator)** 分析 Chunk 内容，决定路由策略。
- **Prompt**: "你是一个流量分发器...如果是纯文字，调用文本法医；如果是公式，调用公式审计员..."
- **Output**: Agent 类型 (`text_forensic` | `formula_auditor` | `layout_architect` | `visual_judge`)

### 4.2 Specialist Agents (专家代理层)
根据协调层的指令，调用相应的专家 Agent 进行验证：

*   **Branch A: 💊 文本法医 Agent**: 检查 OCR 拼写错误、语义连贯性。
*   **Branch B: ➗ 公式审计员 Agent**: 校验 LaTeX 语法、变量一致性。
*   **Branch C: 📐 布局架构师 Agent**: 检查表格完整性、标题层级。
*   **Branch D: 👁️ 视觉法官 Agent**: 全页视觉对比 (需 Vision 能力)。

**Output**: `verification_result` (包含 `valid`, `confidence`, `issues`, `corrected_snippet`)

### 4.3 Refinement & Logic Control (精炼与控制层)

**判断: 置信度检查 (Confidence Check > 99.9%)**

*   **Case 1: YES (Pass)**
    *   将验证后的片段添加到最终输出列表。
    *   更新进度。

*   **Case 2: NO (Fail)**
    *   进入修复循环 (Max 3 attempts):
        1.  调用 **🔧 修复 Agent/Refiner**，传入 `issues` 报告。
        2.  获取 `corrected_md_fragment`。
        3.  **回环**: 重新提交给 Orchestrator 进行再验证。
    *   若 3 次尝试后仍未通过：
        *   标记为 `MANUAL_REVIEW_REQUIRED` (人工复核)。
        *   将当前（可能仍有瑕疵）版本加入输出，并记录日志。

## 5. Result Aggregation & Output (结果汇总与输出)

所有 Chunks 处理完毕后：
1.  **合并**: 将所有处理后的 Chunks 拼接为完整 Markdown。
2.  **输出**: 生成 `final_validated_output.md`。
3.  **报告**: 生成验证过程统计报告 (Total processed, Auto-fixed, Needs Review)。

## 6. Execution Instructions (执行指令)

该流水线通过 Python 脚本 `smart_pipeline_demo.py` 自动执行。

### 运行完整流水线
// turbo-all
1.  确保已配置 `test_data/.env` 和 `pipeline_config.json`。
2.  运行脚本:
    ```powershell
    python smart_pipeline_demo.py
    ```

### 查看结果
1.  检查 `final_validated_output.md`。
