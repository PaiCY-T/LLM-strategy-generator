"""從sandbox_week_test.log恢復1週測試的metrics數據

由於測試在Gen 109被停止，沒有產生export文件。
本腳本從logs中提取可用數據。
"""

import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

log_file = Path("sandbox_week_test.log")
output_file = Path("recovered_week_test_metrics.json")

if not log_file.exists():
    print(f"❌ Log file not found: {log_file}")
    exit(1)

print(f"📖 Reading {log_file}...")

# 數據結構
metrics = []
alerts = defaultdict(list)
template_evolution = defaultdict(lambda: defaultdict(int))

# 正則表達式模式
gen_pattern = re.compile(
    r'Gen (\d+): avg_fitness=([\d.]+), best=([\d.]+), diversity=([\d.]+), champion=(\w+)'
)
alert_pattern = re.compile(
    r'ALERT \[(\w+)\] Gen (\d+): (.+)'
)
template_dist_pattern = re.compile(
    r"Template '(\w+)' dominates at ([\d.]+)%"
)

# 解析log
log_content = log_file.read_text()
for line in log_content.splitlines():
    # 提取generation metrics
    gen_match = gen_pattern.search(line)
    if gen_match:
        gen, avg, best, div, champion = gen_match.groups()
        metrics.append({
            'generation': int(gen),
            'avg_fitness': float(avg),
            'best_fitness': float(best),
            'diversity': float(div),
            'champion_template': champion
        })

    # 提取alerts
    alert_match = alert_pattern.search(line)
    if alert_match:
        severity, gen, message = alert_match.groups()
        alerts[severity].append({
            'generation': int(gen),
            'message': message
        })

        # 提取template分佈信息
        template_match = template_dist_pattern.search(message)
        if template_match:
            template, pct = template_match.groups()
            gen_num = int(gen)
            template_evolution[gen_num][template] = float(pct)

# 統計分析
if metrics:
    print(f"\n✅ 成功恢復 {len(metrics)} 代的metrics數據")
    print(f"   範圍: Gen {metrics[0]['generation']} → Gen {metrics[-1]['generation']}")

    # 關鍵統計
    final_gen = metrics[-1]
    max_fitness_gen = max(metrics, key=lambda x: x['best_fitness'])
    diversity_collapse_gen = next((m for m in metrics if m['diversity'] == 0.0), None)

    print(f"\n📊 關鍵發現:")
    print(f"   最終代數: Gen {final_gen['generation']}")
    print(f"   最終Best Fitness: {final_gen['best_fitness']:.4f}")
    print(f"   最終Avg Fitness: {final_gen['avg_fitness']:.4f}")
    print(f"   最終Diversity: {final_gen['diversity']:.4f}")
    print(f"   最終Champion: {final_gen['champion_template']}")

    print(f"\n   最高Fitness: {max_fitness_gen['best_fitness']:.4f} (Gen {max_fitness_gen['generation']})")

    if diversity_collapse_gen:
        print(f"   Diversity首次歸零: Gen {diversity_collapse_gen['generation']}")

    # Alert統計
    total_alerts = sum(len(v) for v in alerts.values())
    print(f"\n⚠️  總Alert數: {total_alerts}")
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        if severity in alerts:
            print(f"   {severity}: {len(alerts[severity])}")

    # Template演化
    template_counts = defaultdict(int)
    for gen_data in template_evolution.values():
        for template, pct in gen_data.items():
            if pct > 50:  # 主導template
                template_counts[template] += 1

    print(f"\n🧬 Template主導分析:")
    for template, count in sorted(template_counts.items(), key=lambda x: -x[1]):
        print(f"   {template}: 主導 {count} 代")

    # 輸出JSON
    output_data = {
        'metadata': {
            'source': 'sandbox_week_test.log',
            'recovered_at': datetime.now().isoformat(),
            'total_generations': len(metrics),
            'start_generation': metrics[0]['generation'],
            'end_generation': metrics[-1]['generation'],
            'status': 'INCOMPLETE - Test stopped at Gen 109/1000'
        },
        'generation_metrics': metrics,
        'alerts': {
            severity: alerts[severity]
            for severity in alerts
        },
        'template_evolution': {
            str(gen): dist
            for gen, dist in template_evolution.items()
        },
        'summary': {
            'final_generation': final_gen,
            'max_fitness': {
                'value': max_fitness_gen['best_fitness'],
                'generation': max_fitness_gen['generation']
            },
            'diversity_collapse': {
                'first_zero': diversity_collapse_gen['generation'] if diversity_collapse_gen else None
            },
            'alert_counts': {
                severity: len(alerts[severity])
                for severity in alerts
            },
            'template_dominance': dict(template_counts)
        }
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n💾 數據已保存至: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size / 1024:.1f} KB")

else:
    print("❌ 未找到任何metrics數據")

print("\n✅ 恢復完成")
