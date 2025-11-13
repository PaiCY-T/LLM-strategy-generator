LLM策略进化专案系统核心：本系统透过 LLM改善并进化交易策略，并透过多层的验证及回测确保策略品质，开发时请避免过度工程化。

LLM策略进化专案结构规范：
  工作根目录：LLM-strategy-generator/ (此为 Git repository 根目录)

  1. Agent prompt templates 位于：.spec-workflow/agent/
  2. 产品开发 specs 位于：.spec-workflow/specs/
  3. 产品架构 steering docs 位于：.spec-workflow/steering/
  4. 技术文档 位于：docs/

  这些是使用 spec-workflow MCP 系统的关键目录，不要与旧的 .claude/ 目录混淆。

  重要：所有 Claude CLI 会话都应在 LLM-strategy-generator/ 目录下启动。