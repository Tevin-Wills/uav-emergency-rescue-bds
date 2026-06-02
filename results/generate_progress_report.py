"""
Generates the RTK Positioning Module Progress Report as a Word (.docx) document.
Run from any directory — all paths are absolute.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── Paths ────────────────────────────────────────────────────────────────────
BASE       = '/home/tevin_wills2/uav-emergency-rescue-bds'
IMG_L1     = os.path.join(BASE, 'results', 'graphs', 'rtk_positioning', 'level1')
IMG_L2     = os.path.join(BASE, 'results', 'graphs', 'rtk_positioning', 'level2')
OUT_PATH   = '/home/tevin_wills2/uav-emergency-rescue-bds/results/RTK_Positioning_Progress_Report.docx'

doc = Document()

# ── Page margins (2.5 cm all sides) ─────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(2.8)
    section.right_margin  = Cm(2.8)

# ── Style helpers ─────────────────────────────────────────────────────────────
def set_font(run, name='Calibri', size=11, bold=False, italic=False, color=None):
    run.font.name  = name
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def body(text, bold=False, italic=False, size=11, space_after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = Pt(14)
    p.alignment = align
    r = p.add_run(text)
    set_font(r, size=size, bold=bold, italic=italic)
    return p

def heading1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(6)
    r = p.add_run(text)
    set_font(r, size=13, bold=True, color=(31, 73, 125))
    p.paragraph_format.keep_with_next = True
    # bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), '1F497B')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def heading2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    r = p.add_run(text)
    set_font(r, size=11.5, bold=True, color=(54, 96, 146))
    p.paragraph_format.keep_with_next = True
    return p

def heading3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(3)
    r = p.add_run(text)
    set_font(r, size=11, bold=True, italic=True, color=(79, 129, 189))
    p.paragraph_format.keep_with_next = True
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after  = Pt(3)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.left_indent  = Inches(0.25 + level * 0.2)
    r = p.add_run(text)
    set_font(r, size=11)
    return p

def add_figure(img_path, caption_num, caption_text, width=Inches(5.8)):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after  = Pt(2)
    run = p_img.add_run()
    run.add_picture(img_path, width=width)

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after  = Pt(12)
    p_cap.paragraph_format.space_before = Pt(0)
    r_label = p_cap.add_run(f'Figure {caption_num}: ')
    set_font(r_label, size=9.5, bold=True, italic=True)
    r_text = p_cap.add_run(caption_text)
    set_font(r_text, size=9.5, italic=True)

def add_table_row(table, cells_data, header=False, bg_color=None):
    row = table.add_row()
    for i, (cell_text, width) in enumerate(cells_data):
        cell = row.cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(cell_text)
        set_font(r, size=10, bold=header)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if bg_color:
            tcPr = cell._tc.get_or_add_tcPr()
            shd  = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), bg_color)
            tcPr.append(shd)
    return row

def page_break():
    doc.add_page_break()

def spacer(pts=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(pts)
    p.paragraph_format.space_before = Pt(0)

def inline_bold(para_obj, bold_text, normal_text=''):
    r1 = para_obj.add_run(bold_text)
    set_font(r1, bold=True, size=11)
    if normal_text:
        r2 = para_obj.add_run(normal_text)
        set_font(r2, size=11)

# ═══════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ═══════════════════════════════════════════════════════════════════════════
spacer(60)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('UAV Emergency Rescue System')
set_font(r, size=22, bold=True, color=(31, 73, 125))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('RTK Positioning Module')
set_font(r, size=18, bold=True, color=(54, 96, 146))

spacer(8)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('Progress Report')
set_font(r, size=15, bold=False, color=(89, 89, 89))

spacer(40)

for label, value in [
    ('Student', 'Tevin Wills  (Student 1 — RTK Positioning)'),
    ('Module', 'RTK-Based Positioning Subsystem'),
    ('Simulation Stack', 'ROS 2 Jazzy · PX4 SITL · Gazebo · QGroundControl'),
    ('Date', '21 May 2026'),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(5)
    r1 = p.add_run(f'{label}:  ')
    set_font(r1, size=11, bold=True, color=(54, 96, 146))
    r2 = p.add_run(value)
    set_font(r2, size=11)

page_break()

# ═══════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (manual)
# ═══════════════════════════════════════════════════════════════════════════
heading1('Table of Contents')

toc_items = [
    ('1.', 'Executive Summary', '3'),
    ('2.', 'Project Background and Module Scope', '3'),
    ('3.', 'System Architecture', '4'),
    ('4.', 'Level 1 — Standalone Simulation', '4'),
    ('5.', 'Level 2 — PX4/Gazebo Integration', '8'),
    ('6.', 'Challenges and Limitations — Simulation vs. Real RTK Hardware', '13'),
    ('7.', 'Current Status', '15'),
    ('8.', 'Next Steps', '15'),
]

for num, title, pg in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.space_before = Pt(0)
    tab_stops = p.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Inches(5.5), 1)  # right-align at 5.5"
    r1 = p.add_run(f'{num}  {title}')
    set_font(r1, size=10.5)
    r2 = p.add_run(f'\t{pg}')
    set_font(r2, size=10.5)

page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 1. EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
heading1('1.   Executive Summary')

body(
    'This report presents the progress made on the RTK (Real-Time Kinematic) Positioning module '
    'of the UAV Emergency Rescue System. The module is responsible for providing sub-decimetre '
    'positioning accuracy to guide an autonomous UAV to the location of a survivor. Two simulation '
    'levels have been completed. Level 1 validated the RTK algorithm in a standalone ROS 2 '
    'environment, achieving a mean positioning accuracy of 0.101 m compared to a raw GNSS baseline '
    'of 2.394 m — a 95.8% improvement. Level 2 extended this to a full PX4/Gazebo simulation with '
    'an autonomous QGroundControl waypoint mission covering a 208 × 214 m search area, achieving '
    '0.048 m mean error during RTK Fixed lock, representing a 96.7% improvement over raw GNSS and '
    'an 18.8-fold improvement over the autopilot\'s own GPS accuracy estimate of 0.90 m. Both levels '
    'have been logged, analysed, and documented with publication-quality figures. The module is on '
    'schedule for hardware-in-the-loop testing in the next phase.'
)

# ═══════════════════════════════════════════════════════════════════════════
# 2. PROJECT BACKGROUND
# ═══════════════════════════════════════════════════════════════════════════
heading1('2.   Project Background and Module Scope')

body(
    'The UAV Emergency Rescue System is a multi-module team project aimed at developing an '
    'autonomous UAV platform capable of locating and responding to distress signals in '
    'environments where ground-based rescue teams face access constraints. The system integrates '
    'several subsystems including computer vision, mission planning, communication, and positioning. '
    'This report covers the RTK Positioning module exclusively.'
)

body(
    'The objective of the RTK Positioning module is to provide accurate, reliable, and '
    'real-time position estimates to the UAV flight controller, significantly exceeding the '
    'accuracy of standard GNSS. In a rescue scenario, the difference between a 2.4 m positioning '
    'error and a 0.05 m error determines whether the UAV can precisely locate a survivor, '
    'deliver a payload to a specific point, or navigate safely in a constrained space. The module '
    'achieves this by combining raw GNSS measurements with RTCM differential corrections broadcast '
    'from a fixed ground base station.'
)

# ═══════════════════════════════════════════════════════════════════════════
# 3. SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════
heading1('3.   System Architecture')

body(
    'The RTK Positioning module is implemented as a set of ROS 2 nodes communicating over '
    'CycloneDDS. The following nodes form the core of the system:'
)

bullet('Base Station Node — simulates a fixed-position GNSS reference receiver, publishing RTCM differential corrections over the /rtcm/corrections topic.')
bullet('RTCM Correction Simulator Node (Level 2) — models a realistic radio-link correction feed including correction age tracking and deliberate outage events to test system resilience.')
bullet('RTK Positioning Node — the primary processing node. It fuses raw GNSS measurements with RTCM corrections to produce RTK-corrected position estimates, managing fix-state transitions (GNSS Only → RTK Float → RTK Fixed).')
bullet('PX4 Pose Adapter Node (Level 2) — bridges the PX4 SITL flight controller to the ROS 2 graph via MicroXRCEAgent, providing ground truth pose data from the Gazebo physics engine.')
bullet('Logger Node — subscribes to all positioning and ground truth topics and writes timestamped CSV log files for post-flight analysis.')

body(
    'The system runs on ROS 2 Jazzy under Ubuntu 24.04 (Noble) on WSL2. In Level 2, PX4 SITL '
    'and Gazebo run on the same host, with QGroundControl (QGC) connected via UDP for mission '
    'upload and monitoring.'
)

page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 4. LEVEL 1
# ═══════════════════════════════════════════════════════════════════════════
heading1('4.   Level 1 — Standalone Simulation')

heading2('4.1   Experimental Setup')

body(
    'Level 1 validates the RTK algorithm independently of any flight controller, using a '
    'simulated UAV node to generate a deterministic ground truth trajectory. The UAV follows '
    'a 50 × 50 m square path at a fixed altitude of 30 m above ground level (AGL). The '
    'simulation runs at 10 Hz for a total duration of 271.7 seconds, producing 2,718 logged '
    'samples. The data file used for all analysis is rtk_level1_20260521_020841.csv.'
)

body(
    'Raw GNSS measurements are generated by adding Gaussian noise (σ = 1.5 m) to the ground '
    'truth position. RTCM corrections from the base station node progressively improve the '
    'position estimate as the fix state transitions from GNSS Only to RTK Float to RTK Fixed. '
    'All coordinates are expressed in East-North-Up (ENU) metres relative to the base station '
    'at latitude 39.981°N, longitude 116.344°E.'
)

heading2('4.2   RTK Status Progression')

body(
    'The system progresses through three fix states during the Level 1 run. Table 4.1 summarises '
    'the duration, sample count, and positioning accuracy achieved in each state.'
)

# Table 4.1
tbl = doc.add_table(rows=1, cols=5)
tbl.style = 'Table Grid'
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl.paragraph_format = None

hdr_data = [
    ('Phase', 1.2), ('Time Window', 1.2), ('Samples (%)', 1.2),
    ('Raw GNSS Error', 1.4), ('RTK-Corrected Error', 1.6),
]
hdr_row = tbl.rows[0]
for i, (txt, _) in enumerate(hdr_data):
    cell = hdr_row.cells[i]
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(txt)
    set_font(r, size=10, bold=True)
    tcPr = cell._tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '1F497B')
    tcPr.append(shd)
    r.font.color.rgb = RGBColor(255, 255, 255)

rows_data = [
    ['GNSS Only',  '0 – 5 s',    '51  (1.9%)',   '2.121 m', '2.192 m'],
    ['RTK Float',  '5 – 15 s',   '100  (3.7%)',  '2.524 m', '0.389 m'],
    ['RTK Fixed',  '≥ 15 s',     '2,567  (94.4%)','2.394 m', '0.048 m'],
]
alt = False
for rd in rows_data:
    row = tbl.add_row()
    fill = 'D6E4F0' if alt else 'FFFFFF'
    alt  = not alt
    for i, txt in enumerate(rd):
        cell = row.cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(txt)
        set_font(r, size=10)
        tcPr = cell._tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

p_cap = doc.add_paragraph()
p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_cap.paragraph_format.space_before = Pt(4)
p_cap.paragraph_format.space_after  = Pt(10)
r1 = p_cap.add_run('Table 4.1: ')
set_font(r1, size=9.5, bold=True, italic=True)
r2 = p_cap.add_run('RTK fix state distribution and mean positioning error — Level 1 standalone simulation.')
set_font(r2, size=9.5, italic=True)

heading2('4.3   Positioning Accuracy Results')

body(
    'Across the full 271.7-second run, the RTK positioning system achieved a mean 3D error of '
    '0.101 m against simulated ground truth, compared to a raw GNSS mean error of 2.394 m. '
    'This represents a 95.8% reduction in positioning error. During the steady RTK Fixed phase '
    '(94.4% of the run), the mean RTK-corrected error was 0.048 m with a standard deviation of '
    '0.021 m and a 95th-percentile error of 0.085 m.'
)

body(
    'Figure 4.1 shows the full error time series over the 271.7-second run. The raw GNSS error '
    '(red) varies between 0.5 m and 6.2 m, reflecting the Gaussian noise model. The RTK-corrected '
    'error (blue) drops sharply as the fix state progresses, settling near zero once RTK Fixed is '
    'achieved at t = 15 s. The three background shading regions identify the GNSS Only (amber), '
    'RTK Float (yellow), and RTK Fixed (green) phases.'
)

add_figure(
    os.path.join(IMG_L1, 'l1_error_over_time.png'),
    '4.1',
    'RTK positioning error over time — Level 1 standalone simulation. Red: raw GNSS error '
    '(3 s rolling mean). Blue: RTK-corrected error (3 s rolling mean). Dotted lines indicate '
    'overall means. Dashed lines indicate theoretical accuracy specifications per fix state.'
)

body(
    'Figure 4.2 focuses on the first 60 seconds of the run, capturing the complete convergence '
    'sequence from GNSS Only through to RTK Fixed. The lower status strip confirms the timing of '
    'each fix-state transition. The raw GNSS error remains largely unchanged during convergence, '
    'while the RTK-corrected error reduces progressively as more correction data is accumulated.'
)

add_figure(
    os.path.join(IMG_L1, 'l1_rtk_convergence.png'),
    '4.2',
    'RTK fix convergence during the first 60 seconds — Level 1 standalone simulation. '
    'Vertical dotted lines mark the GNSS Only → RTK Float transition at t = 5 s and the '
    'RTK Float → RTK Fixed transition at t = 15 s. The lower strip shows the fix status timeline.'
)

body(
    'Figure 4.3 presents the error distribution for both raw GNSS and RTK-corrected measurements, '
    'using only RTK Fixed samples to represent steady-state performance. The raw GNSS distribution '
    '(left panel) is broad, with a KDE peak near 2.41 m and a 95th-percentile error of 4.18 m. '
    'The RTK-corrected distribution (right panel) is narrow and tightly concentrated near 0.048 m, '
    'with a 95th-percentile error of 0.085 m — confirming consistent sub-decimetre performance '
    'across the steady-state phase.'
)

add_figure(
    os.path.join(IMG_L1, 'l1_error_distribution.png'),
    '4.3',
    'Positioning error distribution during the RTK Fixed period — Level 1 standalone simulation. '
    'Left: raw GNSS error (0–8 m scale). Right: RTK-corrected error (0–0.5 m scale). '
    'Dashed line: mean. Dotted line: median. Dash-dot line: 95th percentile.'
)

body(
    'Figure 4.4 shows the top-down 2D trajectory in the ENU frame. The ground truth path (dark '
    'line) traces the 50 × 50 m square perimeter. The raw GNSS scatter (red) is visibly dispersed '
    'up to several metres around the true path, while the RTK-corrected scatter (blue) is tightly '
    'clustered along the ground truth. The four corner markers (NE, NW, SE, SW) confirm the '
    'planned path geometry was followed correctly throughout the run.'
)

add_figure(
    os.path.join(IMG_L1, 'l1_trajectory.png'),
    '4.4',
    '2D top-down UAV trajectory in the ENU frame — Level 1 standalone simulation. '
    'Dark line: ground truth path. Blue scatter: RTK-corrected positions. '
    'Red scatter: raw GNSS positions. Purple circle: start/end point.'
)

body(
    'Figure 4.5 provides a consolidated performance summary. The left panel compares mean raw '
    'GNSS and RTK-corrected errors side by side for each fix phase. The centre panel shows the '
    'distribution of time spent in each fix state. The right panel shows RTK-corrected error per '
    'phase with standard deviation error bars, and confirms the 95.8% overall accuracy improvement.'
)

add_figure(
    os.path.join(IMG_L1, 'l1_accuracy_summary.png'),
    '4.5',
    'RTK positioning performance summary — Level 1 standalone simulation. '
    'Left: grouped mean error by fix phase (raw GNSS vs RTK-corrected). '
    'Centre: fix state time distribution. Right: RTK-corrected error per fix phase with ±1σ error bars.'
)

page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 5. LEVEL 2
# ═══════════════════════════════════════════════════════════════════════════
heading1('5.   Level 2 — PX4/Gazebo Integration')

heading2('5.1   Experimental Setup')

body(
    'Level 2 extends the standalone simulation by integrating the RTK positioning module with a '
    'full PX4 Software-In-The-Loop (SITL) flight stack running inside Gazebo. The ROS 2 – PX4 '
    'bridge is provided by MicroXRCEAgent over DDS. QGroundControl (QGC) was used to upload and '
    'execute an autonomous waypoint mission consisting of eight waypoints covering a 208 × 214 m '
    'search area at an altitude of 50 m AGL. The mission ran for 166 seconds of active flight. '
    'Six ROS 2 nodes ran concurrently: base station, RTK positioning, RTCM correction simulator, '
    'PX4 pose adapter, logger, and the px4_pose_adapter bridge node.'
)

body(
    'The simulation log captured 10,282 samples at 10 Hz over 1,028 seconds total, including '
    'pre-flight initialisation, the full mission, and post-landing data. The data file used for '
    'analysis is rtk_level2_20260521_022231.csv. The QGC flight log '
    '(qgc_mission_20260521.ulg) was used for independent cross-validation.'
)

heading2('5.2   RTK Status Progression')

body(
    'The system progressed through four distinct fix states during the Level 2 run, including '
    'a deliberate correction outage event. Table 5.1 summarises each phase.'
)

# Table 5.1
tbl2 = doc.add_table(rows=1, cols=5)
tbl2.style = 'Table Grid'
tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER

for i, txt in enumerate(['Phase', 'Time Window', 'Samples (%)', 'Raw GNSS Error', 'RTK-Corrected Error']):
    cell = tbl2.rows[0].cells[i]
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(txt)
    set_font(r, size=10, bold=True)
    r.font.color.rgb = RGBColor(255, 255, 255)
    tcPr = cell._tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '1F497B')
    tcPr.append(shd)

rows2 = [
    ['GNSS Only',        '0 – 5 s',       '50  (0.5%)',    '2.121 m', '2.192 m'],
    ['RTK Float',        '5 – 15 s',      '100  (1.0%)',   '2.524 m', '0.389 m'],
    ['RTK Fixed',        '15–45 s, ≥50 s','10,082  (98.1%)','2.412 m', '0.048 m'],
    ['Correction Lost',  '45 – 50 s',     '50  (0.5%)',    '2.598 m', '3.774 m'],
]
alt = False
for rd in rows2:
    row = tbl2.add_row()
    fill = 'D6E4F0' if alt else 'FFFFFF'
    alt  = not alt
    for i, txt in enumerate(rd):
        cell = row.cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(txt)
        set_font(r, size=10)
        tcPr = cell._tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

p_cap = doc.add_paragraph()
p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_cap.paragraph_format.space_before = Pt(4)
p_cap.paragraph_format.space_after  = Pt(10)
r1 = p_cap.add_run('Table 5.1: ')
set_font(r1, size=9.5, bold=True, italic=True)
r2 = p_cap.add_run('RTK fix state distribution and mean positioning error — Level 2 PX4/Gazebo simulation.')
set_font(r2, size=9.5, italic=True)

body(
    'The Correction Lost phase at t = 45–50 s is a notable event. RTCM corrections were '
    'temporarily unavailable for five seconds, causing the RTK error to spike to a peak of '
    '7.46 m before the system autonomously re-acquired RTK Fixed lock at t = 50 s. This '
    'demonstrates the system\'s resilience under a correction outage — a realistic scenario '
    'in field deployments where base-station radio links can be intermittently disrupted.'
)

heading2('5.3   Positioning Accuracy Results')

body(
    'Across the full 1,028-second run, the RTK positioning system achieved a mean 3D error of '
    '0.080 m against the Gazebo ground truth, compared to a raw GNSS mean error of 2.413 m. '
    'This corresponds to an accuracy improvement of 96.7%. During the steady RTK Fixed phase '
    '(98.1% of the run), the mean error was 0.048 m with a standard deviation of 0.020 m and '
    'a 95th-percentile error of 0.083 m.'
)

body(
    'Figure 5.1 shows the full error time series over the 1,028-second run. The Correction Lost '
    'spike at t = 48.6 s is annotated. Outside this brief event, the RTK-corrected error '
    'remains consistently below 0.15 m throughout the entire mission.'
)

add_figure(
    os.path.join(IMG_L2, 'l2_error_over_time.png'),
    '5.1',
    'RTK positioning error over time — Level 2 PX4/Gazebo simulation. Red: raw GNSS error '
    '(3 s rolling mean). Blue: RTK-corrected error (3 s rolling mean). The annotated spike at '
    't ≈ 49 s corresponds to the Correction Lost event. Background shading identifies the four '
    'fix state phases.'
)

body(
    'Figure 5.2 focuses on the first 60 seconds, capturing all four phase transitions including '
    'the brief Correction Lost period at t = 45–50 s. The status strip at the bottom confirms '
    'the exact timing of each transition. The RTK-corrected error is seen to spike and recover '
    'sharply within the five-second window.'
)

add_figure(
    os.path.join(IMG_L2, 'l2_rtk_convergence.png'),
    '5.2',
    'RTK fix convergence during the first 60 seconds — Level 2 PX4/Gazebo simulation. '
    'All four fix-state transitions are marked. The bottom strip shows the complete status '
    'timeline including the five-second Correction Lost gap at t = 45–50 s.'
)

body(
    'Figure 5.3 shows the error distribution for RTK Fixed samples only, confirming sub-decimetre '
    'steady-state performance. The RTK-corrected distribution (right panel) peaks at 0.047 m '
    'with negligible probability mass beyond 0.15 m. The raw GNSS distribution (left panel) '
    'is broad and centred near 2.41 m, as expected for uncorrected pseudorange measurements.'
)

add_figure(
    os.path.join(IMG_L2, 'l2_error_distribution.png'),
    '5.3',
    'Positioning error distribution during the RTK Fixed period — Level 2 PX4/Gazebo simulation. '
    'Left: raw GNSS error (0–8 m scale). Right: RTK-corrected error (0–0.5 m scale).'
)

body(
    'Figure 5.4 shows the 2D top-down trajectory of the autonomous QGC mission. The mission '
    'covers a significantly larger area than Level 1, spanning 208 m in the East direction and '
    '214 m in the North direction. The RTK-corrected scatter (blue) remains tightly clustered '
    'around the ground truth path (dark line) throughout the full mission extent.'
)

add_figure(
    os.path.join(IMG_L2, 'l2_trajectory.png'),
    '5.4',
    '2D top-down UAV flight trajectory — Level 2 PX4/Gazebo simulation, autonomous QGC mission. '
    'Dark line: ground truth path. Blue scatter: RTK-corrected positions. '
    'Red scatter: raw GNSS positions. Purple circle: home/takeoff point.'
)

body(
    'Figure 5.5 provides the consolidated performance summary for Level 2, including the '
    'four-phase fix state distribution and RTK-corrected error per phase. The Correction Lost '
    'bar clearly shows the degradation to 3.77 m during the outage, contrasting with the '
    '0.048 m achieved during RTK Fixed.'
)

add_figure(
    os.path.join(IMG_L2, 'l2_accuracy_summary.png'),
    '5.5',
    'RTK positioning performance summary — Level 2 PX4/Gazebo simulation. '
    'Left: grouped mean error by fix phase. Centre: four-phase fix state distribution. '
    'Right: RTK-corrected error per phase with ±1σ error bars and overall improvement annotation.'
)

heading2('5.4   QGC ULog Cross-Validation')

body(
    'The QGC flight log (qgc_mission_20260521.ulg) was parsed using the pyulog library to '
    'independently verify the mission trajectory and to benchmark the RTK system against '
    'PX4\'s own GPS accuracy estimate. Three findings are reported.'
)

p = doc.add_paragraph()
p.paragraph_format.space_after  = Pt(4)
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.left_indent  = Inches(0.25)
r = p.add_run('Trajectory confirmation. ')
set_font(r, bold=True, size=11)
r2 = p.add_run(
    'The ground truth path recorded in the ULog matches the Level 2 CSV ground truth geometry '
    '(X range −63.8 to +144.8 m, Y range −81.1 to +133.6 m), confirming that both data sources '
    'describe the same Gazebo simulation flight.'
)
set_font(r2, size=11)

p = doc.add_paragraph()
p.paragraph_format.space_after  = Pt(4)
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.left_indent  = Inches(0.25)
r = p.add_run('PX4 GPS accuracy (EPH). ')
set_font(r, bold=True, size=11)
r2 = p.add_run(
    'The PX4 autopilot reported a horizontal position error estimate (EPH) of 0.90 m '
    'throughout the mission. EPH is the accuracy figure the autopilot uses for its own '
    'navigation decisions and is a standard metric for comparing positioning system performance.'
)
set_font(r2, size=11)

p = doc.add_paragraph()
p.paragraph_format.space_after  = Pt(8)
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.left_indent  = Inches(0.25)
r = p.add_run('RTK advantage over autopilot GPS. ')
set_font(r, bold=True, size=11)
r2 = p.add_run(
    'The RTK system achieved a measured error of 0.048 m during RTK Fixed, which is an '
    '18.8-fold improvement over the autopilot\'s EPH of 0.90 m. In an emergency rescue scenario, '
    'this translates to the difference between locating a survivor within a metre versus '
    'within five centimetres.'
)
set_font(r2, size=11)

body(
    'Figure 5.6 presents the full cross-validation result across three panels: the ULog ground '
    'truth trajectory with PX4 GPS positions and mission waypoints; the three-way accuracy '
    'comparison bar chart (Raw GNSS 2.413 m, PX4 GPS EPH 0.900 m, RTK Fixed 0.048 m); and '
    'the UAV altitude profile from the ULog, confirming the complete mission was executed '
    'correctly with takeoff, cruise at 50 m, and landing.'
)

add_figure(
    os.path.join(IMG_L2, 'l2_qgc_crossval.png'),
    '5.6',
    'QGC ULog cross-validation — Level 2. Left: ULog ground truth trajectory with PX4 GPS '
    'scatter and mission waypoints (triangles). Centre: three-way accuracy comparison '
    '(raw GNSS · PX4 GPS EPH · RTK Fixed). Right: UAV altitude profile confirming autonomous '
    'mission execution with takeoff and landing events marked.'
)

page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 6. CHALLENGES AND LIMITATIONS
# ═══════════════════════════════════════════════════════════════════════════
heading1('6.   Challenges and Limitations — Simulation vs. Real RTK Hardware')

body(
    'A core challenge of this phase of the project is that the RTK positioning module has been '
    'validated entirely within a software simulation environment. While the simulation demonstrates '
    'the correct functional behaviour of the system, several important physical phenomena present '
    'in real RTK deployments are either simplified or absent. Understanding these gaps is essential '
    'for interpreting the results and planning the transition to real hardware.'
)

heading2('6.1   Simplified GNSS Noise Model')

body(
    'The simulation models raw GNSS error as Gaussian noise with a fixed standard deviation '
    '(σ = 1.5 m during GNSS Only, reducing upon RTK convergence). Real GNSS receivers are '
    'affected by multipath interference — signals reflecting off buildings, terrain, and '
    'vegetation before reaching the antenna. Multipath produces non-Gaussian, spatially '
    'correlated errors that cannot be cancelled by RTK corrections. In urban or forested '
    'environments, real raw GNSS errors can reach 5–15 m, far beyond the 2.4 m simulated here.'
)

heading2('6.2   Atmospheric Effects Not Modelled')

body(
    'Real RTK accuracy is influenced by ionospheric and tropospheric delays, which vary with '
    'time of day, season, solar activity, and weather conditions. RTK corrections from a base '
    'station partially cancel these effects for short baselines, but residual errors remain. '
    'Furthermore, real RTK accuracy degrades with baseline distance at approximately 1 part '
    'per million of separation — flying 500 m from the base station introduces roughly '
    '0.5 mm of additional baseline-dependent error. The simulation applies a uniform noise '
    'model regardless of UAV-to-base-station distance, which is unrealistic for longer-range '
    'deployments.'
)

heading2('6.3   Deterministic Convergence vs. Real Integer Ambiguity Resolution')

body(
    'In the simulation, the transition from RTK Float to RTK Fixed occurs deterministically '
    'at t = 15 s. In reality, RTK Fixed requires carrier-phase integer ambiguity resolution — '
    'a mathematically complex process dependent on satellite geometry (PDOP), baseline length, '
    'multipath conditions, and atmospheric stability. Real convergence can take anywhere from '
    '30 seconds to several minutes and can fail entirely in poor conditions, requiring a full '
    're-initialisation. The simulation\'s fixed thresholds do not capture this variability, and '
    'the 15-second convergence time should be understood as a best-case figure rather than a '
    'guaranteed real-world performance target.'
)

heading2('6.4   Communication Link Idealisation')

body(
    'RTCM correction data in a real system is transmitted over a radio link, typically LoRa at '
    '433 or 915 MHz. This link is subject to range limitations, packet loss, channel fading, '
    'and interference from other RF sources on the UAV platform itself. The simulated '
    'Correction Lost event at t = 45–50 s models a correction outage, but the outage is '
    'triggered by a programmatic counter, not a realistic radio channel model. In real '
    'deployments, outages are stochastic in timing and duration, and recovery may not be '
    'instantaneous.'
)

heading2('6.5   Hardware Effects Not Captured')

body('Several physical hardware factors absent from the simulation would affect real-world RTK performance:')

bullet('Antenna phase centre offset and variation — real patch antennas introduce position-dependent errors at low satellite elevation angles, which are not modelled in the simulation.')
bullet('Receiver noise floor — real GNSS receivers have hardware-specific noise characteristics that affect carrier-phase tracking quality and ultimately the achievable RTK accuracy.')
bullet('UAV vibration — mechanical vibration from rotors can cause antenna movement and degrade carrier-phase lock, particularly during aggressive manoeuvres or in windy conditions.')
bullet('Satellite geometry (PDOP) — the simulation uses a fixed noise model independent of satellite count or geometry. In reality, PDOP varies throughout the day and directly affects positioning accuracy.')

heading2('6.6   Implication for Next Steps')

body(
    'The simulation results establish a best-case performance baseline: 0.048 m mean error '
    'under ideal, controlled conditions. Real hardware trials would be expected to show higher '
    'mean errors, longer convergence times, and more frequent correction outages. The next phase '
    'of this module should include hardware-in-the-loop (HIL) testing or real outdoor flights '
    'with a physical RTK base station and rover receiver to quantify the gap between simulated '
    'and measured performance, and to validate that the ROS 2 node architecture integrates '
    'correctly with physical GNSS hardware.'
)

page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 7. CURRENT STATUS
# ═══════════════════════════════════════════════════════════════════════════
heading1('7.   Current Status')

body('Table 7.1 summarises the completion status of all planned RTK positioning module milestones.')

tbl3 = doc.add_table(rows=1, cols=3)
tbl3.style = 'Table Grid'
tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER

for i, txt in enumerate(['Milestone', 'Status', 'Notes']):
    cell = tbl3.rows[0].cells[i]
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(txt)
    set_font(r, size=10, bold=True)
    r.font.color.rgb = RGBColor(255, 255, 255)
    tcPr = cell._tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '1F497B')
    tcPr.append(shd)

status_rows = [
    ('ROS 2 node architecture design',                    '✔  Complete',   'All 6 nodes implemented and tested'),
    ('Level 1 standalone simulation',                     '✔  Complete',   '95.8% accuracy improvement confirmed'),
    ('Level 1 data analysis and figures',                 '✔  Complete',   '5 publication-quality figures generated'),
    ('Level 2 PX4/Gazebo integration',                    '✔  Complete',   'All 6 nodes running with PX4 SITL'),
    ('Level 2 autonomous QGC mission',                    '✔  Complete',   '8-waypoint, 166 s mission executed'),
    ('Level 2 data analysis and figures',                 '✔  Complete',   '6 figures including ULog cross-validation'),
    ('Level 2 GitHub push',                               '⏳  Pending',   'To be committed after report sign-off'),
    ('Integration with other team simulation modules',    '○  Not started','Navigation and mission planning modules'),
    ('RTCM correction model improvement',                 '○  Not started','Variable outage duration and gradual degradation'),
    ('Multipath noise model extension',                   '○  Not started','Spatially correlated error component'),
    ('Level 3 simulation scenario',                       '○  Not started','Complex mission, longer baseline, altitude variation'),
    ('Full system integration test in Gazebo',            '○  Not started','All team modules running simultaneously'),
]
alt = False
for milestone, stat, notes in status_rows:
    row = tbl3.add_row()
    fill = 'D6E4F0' if alt else 'FFFFFF'
    alt  = not alt
    color = '1F7A1F' if '✔' in stat else ('7A5200' if '⏳' in stat else '555555')
    for i, (txt, align) in enumerate([
        (milestone, WD_ALIGN_PARAGRAPH.LEFT),
        (stat,      WD_ALIGN_PARAGRAPH.CENTER),
        (notes,     WD_ALIGN_PARAGRAPH.LEFT),
    ]):
        cell = row.cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = align
        r = p.add_run(txt)
        set_font(r, size=10,
                 bold=(i == 1),
                 color=tuple(int(color[j:j+2], 16) for j in (0,2,4)) if i == 1 else None)
        tcPr = cell._tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

p_cap = doc.add_paragraph()
p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_cap.paragraph_format.space_before = Pt(4)
p_cap.paragraph_format.space_after  = Pt(10)
r1 = p_cap.add_run('Table 7.1: ')
set_font(r1, size=9.5, bold=True, italic=True)
r2 = p_cap.add_run('RTK Positioning module milestone status. ✔ Complete · ⏳ Pending · ○ Not started.')
set_font(r2, size=9.5, italic=True)

# ═══════════════════════════════════════════════════════════════════════════
# 8. NEXT STEPS
# ═══════════════════════════════════════════════════════════════════════════
heading1('8.   Next Steps')

body('The following actions are planned for the next phase of the RTK Positioning module within the simulation environment:')

bullet('Push Level 2 simulation results, analysis scripts, and all generated figures to the team GitHub repository to make the work available to all team members.')
bullet('Integrate the RTK positioning node output with the navigation and mission planning modules being developed by other team members, ensuring that RTK-corrected position data is correctly consumed by the path planner and waypoint controller within the shared simulation environment.')
bullet('Improve the RTCM correction simulation model to introduce more realistic correction outage patterns — including variable outage durations and graduated quality degradation — to better stress-test the system\'s recovery behaviour.')
bullet('Extend the noise model to include a simulated multipath component, where GNSS error is spatially correlated rather than purely Gaussian, to produce more realistic raw GNSS behaviour during trajectory segments near simulated obstacles.')
bullet('Develop a Level 3 simulation scenario that tests the RTK module under a more complex autonomous mission profile, including altitude changes, tighter waypoint spacing, and a longer baseline distance between the base station and the UAV, to evaluate positioning accuracy across a wider range of operating conditions.')
bullet('Conduct a full system-level integration test within the Gazebo environment, running all team modules simultaneously, to verify that the RTK positioning output does not introduce timing or communication bottlenecks across the ROS 2 node graph.')

spacer(20)

# ── Final save ────────────────────────────────────────────────────────────────
doc.save(OUT_PATH)
print(f'Report saved: {OUT_PATH}')
