import sys

def extract_css(filename, out_css):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    start_idx = content.find('st.markdown("""<style>')
    if start_idx == -1: return
    
    end_idx = content.find('</style>', start_idx)
    css_content = content[start_idx + len('st.markdown("""<style>'):end_idx].strip()
    
    with open(out_css, 'w', encoding='utf-8') as f:
        f.write(css_content)

    # find the end of the markdown block
    end_md = content.find('""", unsafe_allow_html=True)', end_idx)
    
    # replace the block
    new_content = content[:start_idx] + 'from core.styles import load_css\nload_css()\n\n# Aurora Background\nst.markdown("""<div class="aurora-bg"></div>""", unsafe_allow_html=True)' + content[end_md + len('""", unsafe_allow_html=True)'):]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)

extract_css('doctor_app/app.py', 'doctor_app/assets/style.css')
extract_css('patient_app/app.py', 'patient_app/assets/style.css')
