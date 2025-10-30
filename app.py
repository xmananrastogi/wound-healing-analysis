#!/usr/bin/env python3
"""
Complete Flask Server - WITH FILTER BUTTONS & TOOLTIPS
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import os
import glob
import json
import subprocess
import threading
import base64
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wound-healing-key'
CORS(app)

analysis_state = {'running': False, 'progress': 0, 'status': ''}


def get_datasets():
    datasets = []
    base_path = 'data/raw/real_dataset'
    if not os.path.exists(base_path):
        return datasets
    for condition in sorted(os.listdir(base_path)):
        cond_path = os.path.join(base_path, condition)
        if os.path.isdir(cond_path):
            for exp in sorted(os.listdir(cond_path)):
                result_path = f"results/real_data/{condition}/{exp}/csv/{exp}_summary.json"
                analyzed = os.path.exists(result_path)
                datasets.append(
                    {'id': f"{condition}/{exp}", 'condition': condition, 'experiment': exp, 'analyzed': analyzed})
    return datasets


def get_results():
    results = []
    summary_files = glob.glob('results/real_data/*/*/csv/*_summary.json')
    for file in sorted(summary_files):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            parts = file.split('/')
            condition = parts[2]
            exp_id = parts[3]
            plot_path = f"results/real_data/{condition}/{exp_id}/plots/{exp_id}_analysis.png"
            csv_path = f"results/real_data/{condition}/{exp_id}/csv/{exp_id}_timeseries.csv"
            if os.path.exists(plot_path):
                csv_data = ""
                chart_data = None
                if os.path.exists(csv_path):
                    with open(csv_path, 'r') as cf:
                        csv_data = cf.read()
                    df = pd.read_csv(csv_path)
                    chart_data = {'time': df['time_hours'].tolist(), 'area': df['wound_area_px'].tolist(),
                                  'closure': df['closure_percentage'].tolist()}
                with open(plot_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode()
                results.append({'id': exp_id, 'condition': condition, 'data': data, 'plot': img_data, 'csv': csv_data,
                                'chart_data': chart_data})
        except Exception as e:
            print(f"Error: {e}")
    return results


def run_analysis(dataset_id, disk_size, time_interval):
    global analysis_state
    try:
        condition, exp_id = dataset_id.split('/')
        input_dir = f"data/raw/real_dataset/{condition}/{exp_id}"
        output_dir = f"results/real_data/{condition}/{exp_id}"
        analysis_state['running'] = True
        analysis_state['progress'] = 0
        analysis_state['status'] = 'Starting analysis...'
        cmd = ['python', 'src/batch_analysis.py', '--input', input_dir, '--output', output_dir, '--disk-size',
               str(disk_size), '--time-interval', str(time_interval), '--visualize']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            analysis_state['progress'] = 100
            analysis_state['status'] = 'Analysis complete!'
        else:
            analysis_state['status'] = f'Error: {stderr}'
    except Exception as e:
        analysis_state['status'] = f'Error: {str(e)}'
    finally:
        analysis_state['running'] = False


@app.route('/')
def index():
    results = get_results()
    datasets = get_datasets()
    total_exp = len(results)
    total_cond = len(set(r['condition'] for r in results))
    total_frames = sum(r['data']['num_timepoints'] for r in results) if results else 0
    total_time = sum(r['data']['processing_time_sec'] for r in results) / 60 if results else 0
    unanalyzed = [d for d in datasets if not d['analyzed']]

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wound Healing - Live Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI'; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding: 20px; }
        .container { max-width: 1800px; margin: 0 auto; }
        .header { background: white; border-radius: 15px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .header h1 { color: #667eea; font-size: 2.5em; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 12px 25px; border: none; background: white; color: #667eea; font-weight: bold; cursor: pointer; border-radius: 5px; }
        .tab-btn.active { background: #667eea; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .live-panel { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 8px; }
        .form-group select, .form-group input { width: 100%; padding: 10px; border: 2px solid #667eea; border-radius: 5px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .btn-primary { background: #667eea; color: white; padding: 12px 30px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        .btn-primary:hover { background: #764ba2; }
        .progress-section { margin-top: 30px; display: none; }
        .progress-section.active { display: block; }
        .progress-bar { width: 100%; height: 30px; background: #f0f0f0; border-radius: 15px; overflow: hidden; margin-bottom: 10px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
        .status { padding: 15px; border-radius: 5px; margin: 10px 0; }
        .status.info { background: #e3f2fd; color: #1976d2; }
        .status.success { background: #e8f5e9; color: #2e7d32; }
        .filter-buttons { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .filter-btn { padding: 10px 20px; border: none; background: white; color: #667eea; font-weight: bold; cursor: pointer; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: all 0.3s; }
        .filter-btn:hover, .filter-btn.active { background: #667eea; color: white; transform: translateY(-2px); }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); text-align: center; }
        .stat-card h3 { color: #667eea; font-size: 2em; }
        .experiments-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }
        @media (max-width: 1400px) { .experiments-grid { grid-template-columns: 1fr; } }
        .experiment-card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .experiment-header { border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 20px; }
        .experiment-header h2 { color: #333; font-size: 1.4em; }
        .condition-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.85em; font-weight: bold; margin-top: 5px; }
        .badge-mdck-control { background: #e3f2fd; color: #1976d2; }
        .badge-mdck-hgf { background: #f3e5f5; color: #7b1fa2; }
        .badge-da3-control { background: #fff3e0; color: #e65100; }
        .badge-da3-hgf { background: #e8f5e9; color: #2e7d32; }
        .plot-container { width: 100%; margin: 20px 0; border-radius: 10px; overflow: hidden; }
        .plot-container img { width: 100%; height: auto; display: block; object-fit: contain; }
        .metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 20px 0; }
        .metric { background: #f5f5f5; padding: 12px; border-radius: 8px; border-left: 4px solid #667eea; position: relative; }
        .metric-label { color: #666; font-size: 0.8em; margin-bottom: 5px; display: block; }
        .metric-value { color: #333; font-size: 1.2em; font-weight: bold; display: block; }
        
        /* Enhanced Aesthetic Design */
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); }
        
        .header { border-top: 5px solid #667eea; }
        .header h1 { background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: 1px; }
        .header p { color: #999; font-size: 1.05em; font-weight: 500; }
        
        .tabs { border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 15px; }
        .tab-btn { border-bottom: 3px solid transparent; border-radius: 0; font-size: 1.05em; transition: all 0.4s ease; }
        .tab-btn.active { border-bottom-color: #667eea; background: transparent; box-shadow: 0 4px 0 #667eea; }
        
        .live-panel { border-top: 5px solid #667eea; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        .live-panel h2 { background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.8em; margin-bottom: 30px; }
        
        .form-group label { color: #667eea; font-weight: 600; font-size: 1.05em; }
        .form-group select, .form-group input { border-radius: 10px; background: #f8f9ff; transition: all 0.3s; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1); }
        .form-group select:focus, .form-group input:focus { outline: none; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25); transform: translateY(-2px); }
        
        .btn-primary { border-radius: 10px; font-size: 1.1em; box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); transition: all 0.3s; }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(102, 126, 234, 0.6); }
        .btn-primary:active { transform: translateY(-1px); }
        
        .progress-fill { font-weight: 700; letter-spacing: 1px; }
        
        .filter-buttons { gap: 15px; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid rgba(255,255,255,0.1); }
        .filter-btn { border-radius: 25px; font-size: 1em; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1); border: 2px solid transparent; }
        .filter-btn:hover { box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); transform: translateY(-3px); }
        .filter-btn.active { box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5); transform: scale(1.05); border-color: #667eea; }
        
        .stat-card { border-radius: 15px; border-top: 4px solid #667eea; transition: all 0.4s; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .stat-card:hover { transform: translateY(-8px); box-shadow: 0 20px 50px rgba(102, 126, 234, 0.3); }
        .stat-card h3 { font-size: 2.5em; font-weight: 800; }
        .stat-card p { color: #999; font-weight: 500; font-size: 1.05em; }
        
        .experiment-card { border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.15); transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1); border: 1px solid rgba(255,255,255,0.1); overflow: hidden; }
        .experiment-card:hover { transform: translateY(-12px); box-shadow: 0 30px 60px rgba(102, 126, 234, 0.4); }
        
        .experiment-header { border-bottom: 3px solid #667eea; padding-bottom: 20px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05)); }
        .experiment-header h2 { font-size: 1.6em; font-weight: 700; }
        
        .condition-badge { font-weight: 600; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
        
        .plot-container { border-radius: 15px; box-shadow: inset 0 2px 8px rgba(0,0,0,0.1); transition: all 0.3s; }
        .plot-container:hover { box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2); }
        
        .metrics-grid { gap: 15px; }
        .metric { border-radius: 12px; border-left: 4px solid #667eea; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.08); cursor: help; }
        .metric:hover { transform: translateY(-4px); box-shadow: 0 12px 25px rgba(102, 126, 234, 0.2); background: #f8faff; }
        .metric-label { color: #667eea; font-weight: 600; font-size: 0.85em; }
        
        .tooltiptext { background: linear-gradient(135deg, #333, #1a1a1a); border-left: 3px solid #667eea; }
        
        .download-btn { border-radius: 10px; font-size: 1em; box-shadow: 0 8px 20px rgba(102, 126, 234, 0.35); transition: all 0.3s; }
        .download-btn:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(102, 126, 234, 0.5); }
        
        /* Smooth Animations */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .experiment-card { animation: fadeIn 0.5s ease forwards; }
        
        /* Glassmorphism effect */
        .live-panel { backdrop-filter: blur(10px); }
        .tooltip { position: relative; display: inline; }
        .tooltiptext { visibility: hidden; width: 200px; background-color: #333; color: #fff; text-align: center; border-radius: 6px; padding: 8px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -100px; opacity: 0; transition: opacity 0.3s; font-size: 0.75em; white-space: normal; }
        .metric:hover .tooltiptext { visibility: visible; opacity: 1; }
        .download-btn { background: #667eea; color: white; padding: 10px 20px; border-radius: 5px; border: none; cursor: pointer; font-weight: bold; margin-top: 15px; }
        .download-btn:hover { background: #764ba2; }
    </style>
</head>
<body>
    <div class="container">
                <div class="header">
            <h1>🔬 Wound Healing Analysis Dashboard</h1>
            <p>✨ Real-time Live Analysis with Advanced Visualization</p>
        </div>


        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('live')">Live Analysis</button>
            <button class="tab-btn" onclick="switchTab('dashboard')">Dashboard</button>
        </div>

        <div id="live" class="tab-content active">
            <div class="live-panel">
                <h2>Live Analysis Panel</h2>

                <div class="form-group">
                    <label>Select Dataset:</label>
                    <select id="datasetSelect">
                        <option value="">-- Choose --</option>
"""

    for d in unanalyzed:
        html += f'                        <option value="{d["id"]}">{d["condition"]} - {d["experiment"]}</option>\n'

    html += f"""                    </select>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Disk Size:</label>
                        <input type="number" id="diskSize" value="10" min="5" max="20">
                    </div>
                    <div class="form-group">
                        <label>Time Interval (hours):</label>
                        <input type="number" id="timeInterval" value="0.25" min="0.1" max="1" step="0.05">
                    </div>
                </div>

                <button class="btn-primary" onclick="startAnalysis()">START ANALYSIS</button>

                <div class="progress-section" id="progressSection">
                    <h3>Progress</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill" style="width: 0%;">0%</div>
                    </div>
                    <div id="statusMessage"></div>
                </div>
            </div>
        </div>

        <div id="dashboard" class="tab-content">
                                    <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterExperiments('all')">🔬 All Experiments</button>
                <button class="filter-btn" onclick="filterExperiments('MDCK_Control')">📊 MDCK Control</button>
                <button class="filter-btn" onclick="filterExperiments('MDCK_HGF')">🧪 MDCK +HGF/SF</button>
                <button class="filter-btn" onclick="filterExperiments('DA3_Control')">📈 DA3 Control</button>
                <button class="filter-btn" onclick="filterExperiments('DA3_HGF')">🔬 DA3 +HGF/SF</button>
                <button class="filter-btn" onclick="filterExperiments('DA3_PHA')">💊 DA3 PHA</button>
            </div>



            <div class="stats-grid">
                <div class="stat-card"><h3>{total_exp}</h3><p>Experiments</p></div>
                <div class="stat-card"><h3>{total_cond}</h3><p>Conditions</p></div>
                <div class="stat-card"><h3>{total_frames}</h3><p>Frames</p></div>
                <div class="stat-card"><h3>{total_time:.1f} min</h3><p>Time</p></div>
            </div>

            <div class="experiments-grid" id="experiments">
"""

    for result in results:
        data = result['data']
        condition = result['condition']
        exp_id = result['id']
        badge_class = f"badge-{condition.lower().replace('_', '-')}"
        csv_b64 = base64.b64encode(result['csv'].encode()).decode()

        html += f"""                <div class="experiment-card" data-condition="{condition}">
                    <div class="experiment-header">
                        <h2>{exp_id}</h2>
                        <span class="condition-badge {badge_class}">{condition.replace('_', ' ')}</span>
                    </div>
                    <div class="plot-container">
                        <img src="data:image/png;base64,{result['plot']}" alt="{exp_id}">
                    </div>
                    <div class="metrics-grid">
                        <div class="metric">
                            <span class="metric-label">Initial Area</span>
                            <span class="metric-value">{data['initial_area_px']:.0f} px</span>
                            <div class="tooltiptext">Wound area at start. Larger = bigger wounds.</div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Final Area</span>
                            <span class="metric-value">{data['final_area_px']:.0f} px</span>
                            <div class="tooltiptext">Wound area at end. Smaller = better healing.</div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Closure</span>
                            <span class="metric-value">{data['final_closure_pct']:.1f}%</span>
                            <div class="tooltiptext">Percentage closed: ((Initial - Final) / Initial) x 100%</div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Healing Rate</span>
                            <span class="metric-value">{abs(data['healing_rate_px_per_hr']):.1f} px/hr</span>
                            <div class="tooltiptext">Speed of closure in pixels per hour.</div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">R2 Value</span>
                            <span class="metric-value">{data['r_squared']:.3f}</span>
                            <div class="tooltiptext">Goodness of fit (0-1). Above 0.7 = good.</div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Frames</span>
                            <span class="metric-value">{data['num_timepoints']}</span>
                            <div class="tooltiptext">Total frames analyzed.</div>
                        </div>
                    </div>
                    <button class="download-btn" onclick="downloadCSV('{exp_id}', '{csv_b64}')">Download CSV</button>
                </div>
"""

    html += """            </div>
        </div>
    </div>

    <script>
        function switchTab(tab) {
            const contents = document.querySelectorAll('.tab-content');
            const buttons = document.querySelectorAll('.tab-btn');
            contents.forEach(el => el.classList.remove('active'));
            buttons.forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
        }

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

        function startAnalysis() {
            const datasetId = document.getElementById('datasetSelect').value;
            if (!datasetId) {
                alert('Select a dataset');
                return;
            }
            document.getElementById('progressSection').classList.add('active');
            document.getElementById('statusMessage').innerHTML = '<div class="status info">Analysis starting...</div>';

            fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    dataset_id: datasetId,
                    disk_size: document.getElementById('diskSize').value,
                    time_interval: document.getElementById('timeInterval').value
                })
            }).then(r => r.json()).then(data => checkProgress());
        }

        function checkProgress() {
            fetch('/api/status').then(r => r.json()).then(data => {
                document.getElementById('progressFill').style.width = data.progress + '%';
                document.getElementById('progressFill').textContent = data.progress + '%';
                document.getElementById('statusMessage').innerHTML = '<div class="status info">' + data.status + '</div>';
                if (data.running) {
                    setTimeout(checkProgress, 1000);
                } else if (data.progress === 100) {
                    document.getElementById('statusMessage').innerHTML = '<div class="status success">Complete! Refreshing...</div>';
                    setTimeout(() => location.reload(), 2000);
                }
            });
        }

        function downloadCSV(filename, data) {
            const csvContent = atob(data);
            const blob = new Blob([csvContent], {type: 'text/csv'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename + '_timeseries.csv';
            a.click();
        }
    </script>
</body>
</html>
"""

    return render_template_string(html)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    global analysis_state
    data = request.json
    dataset_id = data.get('dataset_id')
    disk_size = int(data.get('disk_size', 10))
    time_interval = float(data.get('time_interval', 0.25))
    thread = threading.Thread(target=run_analysis, args=(dataset_id, disk_size, time_interval))
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'started'})


@app.route('/api/status')
def api_status():
    global analysis_state
    return jsonify(analysis_state)


if __name__ == '__main__':
    print("Starting Live Analysis Server...")
    print("=" * 70)
    print("Open: http://localhost:8080")
    print("=" * 70)
    app.run(debug=False, host='0.0.0.0', port=8080)