import streamlit as st
import re

# ==============================================================================
# 🎨 VECTOR ARTWORK (공통 아이콘 리소스)
# ==============================================================================
class ArtWork:
    """모든 페이지에서 공통으로 사용하는 SVG 아이콘 모음"""
    
    @staticmethod
    def get_bear(size=100):
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 100 100" fill="none" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)">
            <circle cx="50" cy="55" r="35" fill="#D6B898"/>
            <circle cx="35" cy="25" r="12" fill="#D6B898"/>
            <circle cx="65" cy="25" r="12" fill="#D6B898"/>
            <circle cx="35" cy="25" r="6" fill="#EAC7A8"/>
            <circle cx="65" cy="25" r="6" fill="#EAC7A8"/>
            <ellipse cx="50" cy="60" rx="14" ry="10" fill="#FFF0F5"/>
            <circle cx="50" cy="56" r="4" fill="#5D4037"/>
            <circle cx="42" cy="48" r="3" fill="#333"/>
            <circle cx="58" cy="48" r="3" fill="#333"/>
            <path d="M50 60V65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/>
            <path d="M46 65C46 65 48 68 50 68C52 68 54 65 54 65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """

    @staticmethod
    def get_book_cover(size=60):
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)">
            <rect x="10" y="8" width="44" height="48" rx="4" fill="#FF9EAA"/>
            <rect x="14" y="8" width="6" height="48" fill="#FF7B8E"/>
            <rect x="24" y="18" width="26" height="4" rx="2" fill="#FFF5F7"/>
            <rect x="24" y="26" width="18" height="4" rx="2" fill="#FFF5F7"/>
            <circle cx="36" cy="42" r="8" fill="#FFD580"/>
        </svg>
        """
    
    @staticmethod
    def get_folder(size=40):
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)">
            <path d="M36 12H20L16 8H4C1.8 8 0 9.8 0 12V32C0 34.2 1.8 36 4 36H36C38.2 36 40 34.2 40 32V16C40 13.8 38.2 12 36 12Z" fill="#A0C4FF"/>
            <path d="M36 16H4V32H36V16Z" fill="#E3F2FD"/>
        </svg>
        """

class Utils:
    @staticmethod
    def clean_html(html_str: str) -> str:
        return re.sub(r'\s+', ' ', html_str).strip()