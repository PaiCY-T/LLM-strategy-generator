#!/bin/bash
# Quick View Script for Design Documents

echo "📄 Design文件快速查看工具"
echo ""
echo "選擇要查看的design文件:"
echo ""
echo "  1. 🔴 Docker Sandbox Security (CRITICAL)"
echo "  2. 🟠 Resource Monitoring System (HIGH)"
echo "  3. 🟠 LLM Integration Activation (HIGH)"
echo "  4. 🟡 Exit Mutation Redesign (MEDIUM)"
echo "  5. 🟡 Structured Innovation MVP (MEDIUM)"
echo "  6. 📚 查看全部概要"
echo "  0. 退出"
echo ""
read -p "輸入選項 (1-6): " choice

case $choice in
  1)
    less /mnt/c/Users/jnpi/documents/finlab/.spec-workflow/specs/docker-sandbox-security/design.md
    ;;
  2)
    less /mnt/c/Users/jnpi/documents/finlab/.spec-workflow/specs/resource-monitoring-system/design.md
    ;;
  3)
    less /mnt/c/Users/jnpi/documents/finlab/.spec-workflow/specs/llm-integration-activation/design.md
    ;;
  4)
    less /mnt/c/Users/jnpi/documents/finlab/.spec-workflow/specs/exit-mutation-redesign/design.md
    ;;
  5)
    less /mnt/c/Users/jnpi/documents/finlab/.spec-workflow/specs/structured-innovation-mvp/design.md
    ;;
  6)
    echo ""
    echo "=== 全部Design概要 ==="
    echo ""
    for spec in docker-sandbox-security resource-monitoring-system llm-integration-activation exit-mutation-redesign structured-innovation-mvp; do
      echo "📁 $spec"
      head -20 /mnt/c/Users/jnpi/documents/finlab/.spec-workflow/specs/$spec/design.md | grep -E "^#|^##"
      echo ""
    done
    ;;
  0)
    echo "退出"
    exit 0
    ;;
  *)
    echo "無效選項"
    ;;
esac
