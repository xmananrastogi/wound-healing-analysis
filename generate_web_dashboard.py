#!/usr/bin/env python3
"""
Generate Interactive Web Dashboard - ALL FEATURES WORKING
"""

import os
import glob
import json
import base64
import pandas as pd


def get_all_results():
    """Collect all analysis results with frames and chart data."""
    results = []
    summary_files = glob.glob('results/real_data/*/*/csv/*_summary.json')

    for file in summary_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)

            parts = file.split('/')
            condition = parts[2]
            exp_id = parts[3]

            plot_path = f"results/real_data/{condition}/{exp_id}/plots/{exp_id}_analysis.png"
            csv_path = f"results/real_data/{condition}/{exp_id}/csv/{exp_id}_timeseries.csv"

            if os.path.exists(plot_path):
                # Read CSV for download AND chart data
                csv_data = ""
                chart_data = None
                if os.path.exists(csv_path):
                    with open(csv_path, 'r') as cf:
                        csv_data = cf.read()

                    # Parse for Chart.js
                    df = pd.read_csv(csv_path)
                    chart_data = {
                        'time': df['time_hours'].tolist(),
                        'area': df['wound_area_px'].tolist(),
                        'closure': df['closure_percentage'].tolist()
                    }

                # Try to find first and last frame images
                frames_dir = os.path.join('results', 'real_data', condition, exp_id, '_extracted_frames')
                first_frame = None
                last_frame = None

                if os.path.exists(frames_dir):
                    frame_files = sorted(glob.glob(os.path.join(frames_dir, '*.png')))
                    if len(frame_files) >= 2:
                        first_frame = frame_files[0]
                        last_frame = frame_files[-1]

                # Encode frames if available
                first_img_b64 = None
                last_img_b64 = None

                if first_frame and os.path.exists(first_frame):
                    with open(first_frame, 'rb') as f:
                        first_img_b64 = base64.b64encode(f.read()).decode()

                if last_frame and os.path.exists(last_frame):
                    with open(last_frame, 'rb') as f:
                        last_img_b64 = base64.b64encode(f.read()).decode()

                results.append({
                    'id': exp_id,
                    'condition': condition,
                    'data': data,
                    'plot': plot_path,
                    'csv': csv_path,
                    'csv_data': csv_data,
                    'chart_data': chart_data,
                    'first_frame': first_img_b64,
                    'last_frame': last_img_b64
                })
        except Exception as e:
            print(f"Error processing {file}: {e}")

    return results


def generate_html(results):
    """Generate HTML dashboard with ALL FEATURES."""

    total_experiments = len(results)
    total_conditions = len(set(r['condition'] for r in results))
    total_frames = sum(r['data']['num_timepoints'] for r in results)
    total_time = sum(r['data']['processing_time_sec'] for r in results) / 60

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wound Healing Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            color: #666;
            font-size: 1.1em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}

        @media (max-width: 1200px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        .stat-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-card h3 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 5px;
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: white;
            color: #667eea;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }}

        .experiments-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin-bottom: 50px;
        }}

        @media (max-width: 1400px) {{
            .experiments-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .experiment-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }}

        .experiment-card:hover {{
            transform: translateY(-5px);
        }}

        .experiment-header {{
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}

        .experiment-header h2 {{
            color: #333;
            font-size: 1.4em;
            margin-bottom: 8px;
        }}

        .condition-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin-top: 5px;
        }}

        .badge-mdck-control {{ background: #e3f2fd; color: #1976d2; }}
        .badge-mdck-hgf {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-da3-control {{ background: #fff3e0; color: #e65100; }}
        .badge-da3-hgf {{ background: #e8f5e9; color: #2e7d32; }}

        /* Tab system */
        .tab-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }}

        .tab-btn {{
            padding: 8px 15px;
            border: none;
            background: #f0f0f0;
            cursor: pointer;
            border-radius: 5px;
            font-size: 0.9em;
            transition: all 0.3s;
        }}

        .tab-btn.active {{
            background: #667eea;
            color: white;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Before/After Slider */
        .comparison-slider {{
            position: relative;
            width: 100%;
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            background: #f0f0f0;
        }}

        .comparison-container {{
            position: relative;
            width: 100%;
            height: 400px;
        }}

        .comparison-img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}

        .overlay-img {{
            clip-path: inset(0 50% 0 0);
        }}

        .slider-handle {{
            position: absolute;
            top: 0;
            left: 50%;
            width: 4px;
            height: 100%;
            background: white;
            cursor: ew-resize;
            transform: translateX(-50%);
            z-index: 10;
        }}

        .slider-button {{
            position: absolute;
            top: 50%;
            left: 50%;
            width: 40px;
            height: 40px;
            background: #667eea;
            border: 3px solid white;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
        }}

        .slider-label {{
            position: absolute;
            bottom: 10px;
            padding: 5px 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            border-radius: 5px;
            font-size: 0.85em;
            z-index: 5;
        }}

        .label-before {{ left: 10px; }}
        .label-after {{ right: 10px; }}

        /* Chart container */
        .chart-container {{
            width: 100%;
            height: 350px;
            margin: 20px 0;
        }}

        /* Plot container */
        .plot-container {{
            width: 100%;
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            background: #f9f9f9;
        }}

        .plot-container img {{
            width: 100%;
            height: auto;
            display: block;
            object-fit: contain;
        }}

        /* Tooltips */
        .metric {{
            background: #f5f5f5;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            position: relative;
            cursor: help;
        }}

        .tooltip {{
            display: none;
            position: absolute;
            background: #333;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.85em;
            width: 220px;
            z-index: 1000;
            bottom: 110%;
            left: 50%;
            transform: translateX(-50%);
        }}

        .tooltip::after {{
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 8px solid transparent;
            border-top-color: #333;
        }}

        .metric:hover .tooltip {{
            display: block;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin: 20px 0;
        }}

        .metric-label {{
            color: #666;
            font-size: 0.8em;
            margin-bottom: 5px;
            display: block;
        }}

        .metric-value {{
            color: #333;
            font-size: 1.2em;
            font-weight: bold;
            display: block;
        }}

        .button-group {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}

        .download-btn {{
            flex: 1;
            min-width: 140px;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            border: none;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .download-btn:hover {{
            background: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Wound Healing Analysis Dashboard</h1>
            <p>Interactive Analysis with Before/After Slider, Tooltips & Live Charts</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>{total_experiments}</h3>
                <p>Total Experiments</p>
            </div>
            <div class="stat-card">
                <h3>{total_conditions}</h3>
                <p>Conditions</p>
            </div>
            <div class="stat-card">
                <h3>{total_frames}</h3>
                <p>Total Frames</p>
            </div>
            <div class="stat-card">
                <h3>{total_time:.1f} min</h3>
                <p>Processing Time</p>
            </div>
        </div>

        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterExperiments('all')">🔬 All Experiments</button>
            <button class="filter-btn" onclick="filterExperiments('MDCK_Control')">📊 MDCK Control</button>
            <button class="filter-btn" onclick="filterExperiments('MDCK_HGF')">🧪 MDCK +HGF/SF</button>
            <button class="filter-btn" onclick="filterExperiments('DA3_Control')">📈 DA3 Control</button>
            <button class="filter-btn" onclick="filterExperiments('DA3_HGF')">🔬 DA3 +HGF/SF</button>
        </div>

        <div class="experiments-grid" id="experiments">
"""

    for idx, result in enumerate(results):
        data = result['data']
        condition = result['condition']
        exp_id = result['id']
        badge_class = f"badge-{condition.lower().replace('_', '-')}"

        csv_b64 = base64.b64encode(result['csv_data'].encode()).decode()

        with open(result['plot'], 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()

        chart_json = json.dumps(result['chart_data']) if result['chart_data'] else 'null'

        html += f"""
            <div class="experiment-card" data-condition="{condition}">
                <div class="experiment-header">
                    <h2>{exp_id}</h2>
                    <span class="condition-badge {badge_class}">{condition.replace('_', ' ')}</span>
                </div>

                <div class="tab-buttons">
                    <button class="tab-btn active" onclick="showTab('{exp_id}', 'plot')">📈 Analysis Plot</button>
"""

        if result['chart_data']:
            html += f"""                    <button class="tab-btn" onclick="showTab('{exp_id}', 'chart')">📊 Interactive Chart</button>
"""

        if result['first_frame'] and result['last_frame']:
            html += f"""                    <button class="tab-btn" onclick="showTab('{exp_id}', 'comparison')">📸 Before/After</button>
"""

        html += """                </div>

"""

        # Plot tab (default)
        html += f"""                <div id="{exp_id}-plot" class="tab-content active">
                    <div class="plot-container">
                        <img src="data:image/png;base64,{img_data}" alt="{exp_id} analysis">
                    </div>
                </div>
"""

        # Chart tab
        if result['chart_data']:
            html += f"""                <div id="{exp_id}-chart" class="tab-content">
                    <div class="chart-container">
                        <canvas id="chart-{exp_id}"></canvas>
                    </div>
                </div>
"""

        # Before/After tab
        if result['first_frame'] and result['last_frame']:
            total_time_hrs = data['num_timepoints'] * 0.25
            html += f"""                <div id="{exp_id}-comparison" class="tab-content">
                    <div class="comparison-slider">
                        <div class="comparison-container" id="{exp_id}-container">
                            <img src="data:image/png;base64,{result['first_frame']}" class="comparison-img" alt="Before">
                            <img src="data:image/png;base64,{result['last_frame']}" class="comparison-img overlay-img" id="{exp_id}-overlay" alt="After">
                            <div class="slider-handle" id="{exp_id}-handle">
                                <div class="slider-button">⟷</div>
                            </div>
                            <div class="slider-label label-before">T = 0 hrs</div>
                            <div class="slider-label label-after">T = {total_time_hrs:.1f} hrs</div>
                        </div>
                    </div>
                </div>
"""

        # Metrics with tooltips
        html += f"""                
                <div class="metrics-grid">
                    <div class="metric">
                        <span class="metric-label">Initial Area</span>
                        <span class="metric-value">{data['initial_area_px']:.0f} px</span>
                        <div class="tooltip">Wound area at the start (T=0). Larger values indicate bigger initial wounds.</div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Final Area</span>
                        <span class="metric-value">{data['final_area_px']:.0f} px</span>
                        <div class="tooltip">Wound area at the end. Smaller values indicate better healing.</div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Closure</span>
                        <span class="metric-value">{data['final_closure_pct']:.1f}%</span>
                        <div class="tooltip">Percentage of wound closed. Formula: ((Initial - Final) / Initial) × 100%</div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Healing Rate</span>
                        <span class="metric-value">{abs(data['healing_rate_px_per_hr']):.1f} px/hr</span>
                        <div class="tooltip">Speed of wound closure in pixels per hour. Higher = faster healing.</div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">R² Value</span>
                        <span class="metric-value">{data['r_squared']:.3f}</span>
                        <div class="tooltip">Goodness of fit (0-1). Values >0.7 indicate good linear correlation.</div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Frames</span>
                        <span class="metric-value">{data['num_timepoints']}</span>
                        <div class="tooltip">Number of time-lapse frames analyzed. Each frame = 15 minutes.</div>
                    </div>
                </div>

                <div class="button-group">
                    <button class="download-btn" onclick="downloadCSV('{exp_id}', '{csv_b64}')">📥 Download CSV</button>
                </div>
            </div>
"""

        # JavaScript for this card
        if result['chart_data']:
            html += f"""
        <script>
            (function() {{
                const chartData = {chart_json};
                if (chartData && chartData.time) {{
                    const ctx = document.getElementById('chart-{exp_id}').getContext('2d');
                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: chartData.time.map(t => t.toFixed(1) + ' hrs'),
                            datasets: [{{
                                label: 'Wound Area (px)',
                                data: chartData.area,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                tension: 0.4,
                                yAxisID: 'y'
                            }}, {{
                                label: 'Closure (%)',
                                data: chartData.closure,
                                borderColor: '#764ba2',
                                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                                tension: 0.4,
                                yAxisID: 'y1'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {{
                                mode: 'index',
                                intersect: false
                            }},
                            plugins: {{
                                title: {{
                                    display: true,
                                    text: '{exp_id} - Healing Progress'
                                }}
                            }},
                            scales: {{
                                y: {{
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: {{
                                        display: true,
                                        text: 'Wound Area (pixels)'
                                    }}
                                }},
                                y1: {{
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: {{
                                        display: true,
                                        text: 'Closure (%)'
                                    }},
                                    grid: {{
                                        drawOnChartArea: false
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
            }})();
        </script>
"""

        # Before/After slider JavaScript
        if result['first_frame'] and result['last_frame']:
            html += f"""
        <script>
            (function() {{
                const handle = document.getElementById('{exp_id}-handle');
                const overlay = document.getElementById('{exp_id}-overlay');
                const container = document.getElementById('{exp_id}-container');

                if (handle && overlay && container) {{
                    handle.addEventListener('mousedown', function(e) {{
                        const move = (e) => {{
                            const rect = container.getBoundingClientRect();
                            const x = e.clientX - rect.left;
                            const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
                            handle.style.left = percent + '%';
                            overlay.style.clipPath = `inset(0 ${{100 - percent}}% 0 0)`;
                        }};

                        document.addEventListener('mousemove', move);
                        document.addEventListener('mouseup', () => {{
                            document.removeEventListener('mousemove', move);
                        }}, {{ once: true }});

                        e.preventDefault();
                    }});
                }}
            }})();
        </script>
"""

    html += """
        </div>
    </div>

    <script>
        function filterExperiments(condition) {
            const cards = document.querySelectorAll('.experiment-card');
            const buttons = document.querySelectorAll('.filter-btn');

            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            cards.forEach(card => {
                if (condition === 'all' || card.dataset.condition === condition) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function showTab(expId, tabName) {
            ['plot', 'chart', 'comparison'].forEach(tab => {
                const content = document.getElementById(`${expId}-${tab}`);
                const btn = document.querySelector(`button[onclick="showTab('${expId}', '${tab}')"]`);
                if (content) content.classList.remove('active');
                if (btn) btn.classList.remove('active');
            });

            const content = document.getElementById(`${expId}-${tabName}`);
            const btn = document.querySelector(`button[onclick="showTab('${expId}', '${tabName}')"]`);
            if (content) content.classList.add('active');
            if (btn) btn.classList.add('active');
        }

        function downloadCSV(filename, data) {
            const csvContent = atob(data);
            const blob = new Blob([csvContent], {type: 'text/csv'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename + '_timeseries.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""

    return html


def main():
    print("🌐 Generating Final Dashboard with ALL Features...")
    print("=" * 70)

    results = get_all_results()

    if len(results) == 0:
        print("❌ No results found!")
        return

    print(f"✓ Found {len(results)} experiments")

    # Check for chart data
    has_charts = sum(1 for r in results if r['chart_data'])
    has_frames = sum(1 for r in results if r['first_frame'] and r['last_frame'])

    print(f"✓ {has_charts} experiments with interactive charts")
    print(f"✓ {has_frames} experiments with before/after slider")
    print("✓ All experiments have tooltips")

    html = generate_html(results)

    output_path = 'results/dashboard.html'
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"\n✅ Dashboard generated!")
    print(f"📄 File: {output_path}")
    print(f"\n🎉 Features included:")
    print("   ✓ Analysis plots (all experiments)")
    print(f"   ✓ Interactive Chart.js charts ({has_charts} experiments)")
    print(f"   ✓ Before/After sliders ({has_frames} experiments)")
    print("   ✓ Metric tooltips (hover to see)")
    print("   ✓ CSV download (working)")
    print(f"\n🌐 Open: open {output_path}")


if __name__ == "__main__":
    main()