#!/bin/bash
# Spec Workflow Design Approval Script
# 用於批准待審核的design文件

WORKFLOW_ROOT="/mnt/c/Users/jnpi/documents/finlab/.spec-workflow"
APPROVALS_DIR="$WORKFLOW_ROOT/approvals"

echo "🔍 檢查待審核的design文件..."
echo ""

# 審核ID列表
APPROVALS=(
  "docker-sandbox-security/approval_1761343967133_xyzxns2y0.json"
  "resource-monitoring-system/approval_1761344139064_s1dfkszq2.json"
  "llm-integration-activation/approval_1761344417779_e49k8cpn9.json"
  "exit-mutation-redesign/approval_1761344569933_y4b3x95tn.json"
  "structured-innovation-mvp/approval_1761344570089_az0b5wc80.json"
)

# 顯示待審核列表
echo "📋 待審核的Design文件 (5個):"
echo ""
for approval in "${APPROVALS[@]}"; do
  approval_file="$APPROVALS_DIR/$approval"
  if [ -f "$approval_file" ]; then
    title=$(grep -o '"title": "[^"]*"' "$approval_file" | cut -d'"' -f4)
    status=$(grep -o '"status": "[^"]*"' "$approval_file" | cut -d'"' -f4)
    echo "  ✓ $title"
    echo "    狀態: $status"
    echo ""
  fi
done

echo ""
echo "❓ 您要批准所有5個design文件嗎？"
echo "   這將允許繼續進行tasks.md的創建"
echo ""
read -p "輸入 'yes' 確認批准，或按Enter取消: " confirm

if [ "$confirm" != "yes" ]; then
  echo "❌ 已取消"
  exit 0
fi

echo ""
echo "✅ 正在批准所有design文件..."
echo ""

# 批准每個文件
for approval in "${APPROVALS[@]}"; do
  approval_file="$APPROVALS_DIR/$approval"

  if [ -f "$approval_file" ]; then
    # 修改status為approved，並添加approvedAt時間戳
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

    # 使用sed替換status和添加approvedAt
    sed -i "s/\"status\": \"pending\"/\"status\": \"approved\"/" "$approval_file"
    sed -i "s/\"createdAt\":/\"approvedAt\": \"$timestamp\",\n  \"createdAt\":/" "$approval_file"

    title=$(grep -o '"title": "[^"]*"' "$approval_file" | cut -d'"' -f4)
    echo "  ✅ 已批准: $title"
  else
    echo "  ⚠️  未找到: $approval_file"
  fi
done

echo ""
echo "🎉 完成！所有design文件已批准"
echo ""
echo "📝 下一步:"
echo "   1. 回到Claude Code"
echo "   2. 告訴Claude: '已批准' 或 '審核完成'"
echo "   3. Claude會檢查狀態並繼續創建tasks.md"
echo ""
