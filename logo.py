import streamlit as st
from typing import Literal
import base64

def get_animated_logo_html():
    """Returns HTML with embedded CSS animations with spaceship orbiting the logo"""
    return """
    <style>
        @keyframes orbit {
            0% {
                transform: rotate(0deg) translateX(60px) rotate(0deg);
                opacity: 1;
            }
            50% {
                opacity: 0.8;
            }
            100% {
                transform: rotate(360deg) translateX(60px) rotate(-360deg);
                opacity: 1;
            }
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
        }
        @keyframes flame {
            0% { height: 8px; opacity: 0.9; }
            50% { height: 12px; opacity: 0.6; }
            100% { height: 8px; opacity: 0.9; }
        }
        
        :root {
            --neon-green: #00FF7F;
            --dark-bg: #0D0208;
            --spaceship-color: #00F5FF;
        }
        
        .logo-header-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        
        .logo-container {
            width: 120px;
            height: 120px;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .logo-circle {
            position: absolute;
            width: 80px;
            height: 80px;
            top: 20px;
            left: 20px;
            border-radius: 50%;
            border: 2px dashed var(--neon-green);
            animation: rotate 20s linear infinite;
        }
        
        .logo-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: var(--neon-green);
            font-family: Arial, sans-serif;
            font-weight: bold;
            font-size: 14px;
            text-align: center;
            animation: pulse 2s ease-in-out infinite;
            white-space: nowrap;
        }
        
        .logo-bg {
            position: absolute;
            width: 100%;
            height: 100%;
            background: var(--dark-bg);
            border: 1px solid var(--neon-green);
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
        }
        
        .spaceship {
            position: absolute;
            width: 12px;
            height: 12px;
            background-color: var(--spaceship-color);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--spaceship-color);
            animation: orbit 5s linear infinite;
            top: 50%;
            left: 50%;
            margin-top: -6px;
            margin-left: -6px;
        }
        
        .spaceship::after {
            content: '';
            position: absolute;
            bottom: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 4px;
            height: 8px;
            background: linear-gradient(to bottom, #FF4500, transparent);
            border-radius: 50% 50% 0 0;
            animation: flame 0.5s ease-in-out infinite alternate;
        }
        
        .orbit-path {
            position: absolute;
            width: 140px;
            height: 100px;
            top: 10px;
            left: -10px;
            border: 1px dashed rgba(0, 255, 127, 0.3);
            border-radius: 70px / 50px;
        }
        
        .title-container {
            text-align: center;
        }
        
        .main-title {
            color: var(--neon-green);
            font-size: 2.5rem;
            margin: 0;
            text-shadow: 0 0 10px rgba(0, 255, 127, 0.7);
        }
        
        .subtitle {
            color: rgba(240, 248, 255, 0.8);
            margin: 0;
            font-size: 1.1rem;
        }
        
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .logo-container:hover {
            transform: scale(1.1);
        }
        
        .logo-container:hover .logo-circle {
            border-width: 3px;
            box-shadow: 0 0 15px var(--neon-green);
        }
        
        .logo-container:hover ~ .spaceship {
            animation-duration: 3s;
        }
    </style>
    
    <div class="logo-header-container">
        <div class="logo-container">
            <div class="logo-bg"></div>
            <div class="orbit-path"></div>
            <div class="logo-circle"></div>
            <div class="spaceship"></div>
            <div class="logo-text">JOBFINDER<br>PRO+</div>
        </div>
        
        <div class="title-container">
            <h1 class="main-title">🔍 JobFinder Pro+</h1>
            <p class="subtitle">The Next-Gen AI-Powered Career Revolution</p>
        </div>
    </div>
    """

def show_animated_logo():
    """Renders the animated logo with integrated header using Streamlit components"""
    st.components.v1.html(
        get_animated_logo_html(),
        height=180
    )