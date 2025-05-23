import json
from pathlib import Path
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Table, 
                               TableStyle, Spacer, Image)
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit as st
import base64

class ProfessionalResumeBuilder:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles for professional resumes"""
        style_definitions = {
            'Header': {
                'parent': self.styles['Heading1'],
                'fontSize': 16,
                'leading': 18,
                'spaceAfter': 6,
                'textColor': colors.HexColor("#2E5D9E")
            },
            'SectionHeader': {
                'parent': self.styles['Heading2'],
                'fontSize': 12,
                'leading': 14,
                'spaceAfter': 6,
                'textColor': colors.HexColor("#2E5D9E"),
                'underline': True
            },
            'JobTitle': {
                'parent': self.styles['Normal'],
                'fontSize': 11,
                'leading': 13,
                'textColor': colors.black,
                'fontName': 'Helvetica-Bold'
            },
            'Company': {
                'parent': self.styles['Normal'],
                'fontSize': 10,
                'leading': 12,
                'textColor': colors.HexColor("#555555"),
                'fontName': 'Helvetica-Bold'
            },
            'Date': {
                'parent': self.styles['Normal'],
                'fontSize': 9,
                'leading': 11,
                'textColor': colors.HexColor("#777777"),
                'fontName': 'Helvetica-Oblique'
            },
            'Bullet': {
                'parent': self.styles['Normal'],
                'fontSize': 10,
                'leading': 12,
                'leftIndent': 10,
                'spaceBefore': 3,
                'bulletIndent': 0,
                'textColor': colors.black
            }
        }

        for name, params in style_definitions.items():
            if not hasattr(self.styles, name):
                self.styles.add(ParagraphStyle(name=name, **params))
            else:
                # Update existing style
                for param, value in params.items():
                    setattr(self.styles[name], param, value)

    def create_resume_pdf(self, resume_data, template="modern"):
        """Create professional resume PDF based on template"""
        buffer = BytesIO()
        
        if template == "modern":
            doc = self._create_modern_resume(buffer, resume_data)
        elif template == "classic":
            doc = self._create_classic_resume(buffer, resume_data)
        else:
            doc = self._create_executive_resume(buffer, resume_data)
        
        buffer.seek(0)
        return buffer

    def _create_modern_resume(self, buffer, resume_data):
        """Modern clean layout with subtle colors"""
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )
        
        elements = []
        
        # Header section
        header_table = Table([
            [Paragraph(f"<b>{resume_data['name']}</b>", self.styles['Header']), ""],
            [resume_data['email'], resume_data['phone']]
        ], colWidths=[4*inch, 2*inch])
        
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (0, 0), 1, colors.HexColor("#2E5D9E")),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor("#2E5D9E")),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Professional Summary
        if resume_data.get('summary'):
            elements.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeader']))
            elements.append(Paragraph(resume_data['summary'], self.styles['Normal']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Work Experience
        if resume_data.get('experience'):
            elements.append(Paragraph("PROFESSIONAL EXPERIENCE", self.styles['SectionHeader']))
            
            for exp in resume_data['experience']:
                # Job title and date
                job_header = Table([
                    [
                        Paragraph(exp['title'], self.styles['JobTitle']),
                        Paragraph(f"{exp['start']} - {exp['end']}", self.styles['Date'])
                    ],
                    [Paragraph(exp['company'], self.styles['Company']), ""]
                ], colWidths=[4*inch, 2*inch])
                
                job_header.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT')
                ]))
                
                elements.append(job_header)
                
                # Job description bullets
                if exp.get('description'):
                    bullets = exp['description'].split('\n')
                    for bullet in bullets:
                        if bullet.strip():
                            elements.append(Paragraph(f"• {bullet.strip()}", self.styles['Bullet']))
                
                elements.append(Spacer(1, 0.1*inch))
        
        # Education
        if resume_data.get('education'):
            elements.append(Paragraph("EDUCATION", self.styles['SectionHeader']))
            
            for edu in resume_data['education']:
                edu_table = Table([
                    [
                        Paragraph(edu['degree'], self.styles['JobTitle']),
                        Paragraph(edu['year'], self.styles['Date'])
                    ],
                    [Paragraph(edu['institution'], self.styles['Company']), ""]
                ], colWidths=[4*inch, 2*inch])
                
                edu_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT')
                ]))
                
                elements.append(edu_table)
                elements.append(Spacer(1, 0.1*inch))
        
        # Skills
        if resume_data.get('skills'):
            elements.append(Paragraph("SKILLS & COMPETENCIES", self.styles['SectionHeader']))
            
            # Create a grid of skills (3 columns)
            skills = resume_data['skills']
            skill_rows = [skills[i:i+3] for i in range(0, len(skills), 3)]
            
            skill_table = Table(skill_rows, colWidths=[2*inch, 2*inch, 2*inch])
            skill_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LEADING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            elements.append(skill_table)
        
        doc.build(elements)
        return doc

    def _create_classic_resume(self, buffer, resume_data):
        """Traditional two-column resume format"""
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )
        
        elements = []
        
        # Header
        elements.append(Paragraph(resume_data['name'], self.styles['Heading1']))
        elements.append(Spacer(1, 0.1*inch))
        
        contact_info = f"{resume_data['email']} | {resume_data['phone']}"
        elements.append(Paragraph(contact_info, self.styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Two-column layout
        two_col = Table([
            [
                self._create_left_column(resume_data),
                self._create_right_column(resume_data)
            ]
        ], colWidths=[3.5*inch, 2.5*inch])
        
        two_col.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (1, 0), (1, 0), 0)
        ]))
        
        elements.append(two_col)
        doc.build(elements)
        return doc

    def _create_left_column(self, resume_data):
        """Left column content for classic resume"""
        left_elements = []
        
        # Professional Summary
        if resume_data.get('summary'):
            left_elements.append(Paragraph("SUMMARY", self.styles['Heading2']))
            left_elements.append(Paragraph(resume_data['summary'], self.styles['Normal']))
            left_elements.append(Spacer(1, 0.2*inch))
        
        # Experience
        if resume_data.get('experience'):
            left_elements.append(Paragraph("EXPERIENCE", self.styles['Heading2']))
            
            for exp in resume_data['experience']:
                left_elements.append(Paragraph(exp['title'], self.styles['Heading3']))
                left_elements.append(Paragraph(exp['company'], self.styles['Italic']))
                
                date_str = f"{exp['start']} - {exp['end']}"
                left_elements.append(Paragraph(date_str, self.styles['Italic']))
                
                if exp.get('description'):
                    bullets = exp['description'].split('\n')
                    for bullet in bullets:
                        if bullet.strip():
                            left_elements.append(Paragraph(f"• {bullet.strip()}", self.styles['Normal']))
                
                left_elements.append(Spacer(1, 0.1*inch))
        
        return left_elements

    def _create_right_column(self, resume_data):
        """Right column content for classic resume"""
        right_elements = []
        
        # Skills
        if resume_data.get('skills'):
            right_elements.append(Paragraph("SKILLS", self.styles['Heading2']))
            
            for skill in resume_data['skills']:
                right_elements.append(Paragraph(f"• {skill}", self.styles['Normal']))
            
            right_elements.append(Spacer(1, 0.2*inch))
        
        # Education
        if resume_data.get('education'):
            right_elements.append(Paragraph("EDUCATION", self.styles['Heading2']))
            
            for edu in resume_data['education']:
                right_elements.append(Paragraph(edu['degree'], self.styles['Normal']))
                right_elements.append(Paragraph(edu['institution'], self.styles['Italic']))
                right_elements.append(Paragraph(edu['year'], self.styles['Italic']))
                right_elements.append(Spacer(1, 0.1*inch))
        
        return right_elements

    def _create_executive_resume(self, buffer, resume_data):
        """Premium executive resume format"""
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )
        
        elements = []
        
        # Header with accent color
        header_table = Table([
            [
                Paragraph(f"<font size=14 color=#FFFFFF><b>{resume_data['name']}</b></font>", 
                         self.styles['Normal']),
            ]
        ], colWidths=[7*inch], rowHeights=[0.5*inch])
        
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#2E5D9E")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#2E5D9E"))
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Contact info
        contact_table = Table([
            [
                Paragraph(f"<b>Email:</b> {resume_data['email']}", self.styles['Normal']),
                Paragraph(f"<b>Phone:</b> {resume_data['phone']}", self.styles['Normal'])
            ]
        ], colWidths=[3.5*inch, 3.5*inch])
        
        elements.append(contact_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Professional Profile
        if resume_data.get('summary'):
            elements.append(Paragraph("<b>PROFESSIONAL PROFILE</b>", self.styles['Heading2']))
            elements.append(Paragraph(resume_data['summary'], self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Core Competencies
        if resume_data.get('skills'):
            elements.append(Paragraph("<b>CORE COMPETENCIES</b>", self.styles['Heading2']))
            
            # Create a grid of skills with bullet points
            skills = [f"• {skill}" for skill in resume_data['skills']]
            skill_table = Table([skills[i:i+2] for i in range(0, len(skills), 2)], 
                              colWidths=[3.5*inch, 3.5*inch])
            
            skill_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEADING', (0, 0), (-1, -1), 14)
            ]))
            
            elements.append(skill_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Professional Experience
        if resume_data.get('experience'):
            elements.append(Paragraph("<b>PROFESSIONAL EXPERIENCE</b>", self.styles['Heading2']))
            
            for exp in resume_data['experience']:
                # Position and company
                elements.append(Paragraph(
                    f"<b>{exp['title']}</b> | <i>{exp['company']}</i>", 
                    self.styles['Normal']
                ))
                
                # Dates
                elements.append(Paragraph(
                    f"{exp['start']} - {exp['end']}", 
                    self.styles['Italic']
                ))
                
                # Description
                if exp.get('description'):
                    bullets = exp['description'].split('\n')
                    for bullet in bullets:
                        if bullet.strip():
                            elements.append(Paragraph(
                                f"‣ {bullet.strip()}", 
                                self.styles['Normal']
                            ))
                
                elements.append(Spacer(1, 0.1*inch))
        
        # Education
        if resume_data.get('education'):
            elements.append(Paragraph("<b>EDUCATION & QUALIFICATIONS</b>", self.styles['Heading2']))
            
            for edu in resume_data['education']:
                elements.append(Paragraph(
                    f"<b>{edu['degree']}</b>, {edu['institution']} ({edu['year']})", 
                    self.styles['Normal']
                ))
        
        doc.build(elements)
        return doc

    def get_resume_templates(self):
        """Return available resume templates"""
        return {
            "Modern": "modern",
            "Classic": "classic",
            "Executive": "executive"
        }

    def create_download_button(self, pdf_bytes, file_name="resume.pdf"):
        """Create a download button for the resume"""
        b64 = base64.b64encode(pdf_bytes.getvalue()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">Download Resume</a>'
        st.markdown(href, unsafe_allow_html=True)