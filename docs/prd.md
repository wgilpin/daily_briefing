# Personal Intelligence Digest - Product Requirements Document

## Product Overview

A local-first application that aggregates and curates daily content from personal information sources into a unified, intelligent digest.

## Problem Statement

Information fragmentation across multiple platforms creates cognitive overhead and missed insights. Professionals need a personalized, privacy-preserving solution to synthesize their daily information diet without relying on cloud services.
Core Features

## Content Ingestion Pipeline

- Gmail Integration: OAuth-based newsletter extraction with sender/subject pattern recognition
- Twitter/X API: Timeline fetch with configurable depth (e.g., last 24h)
- Zotero Sync: Monitor library additions via local SQLite or API sync
- News Aggregation: RSS/API feeds from configurable sources

## Intelligence Layer

Topic Labelling: Extract and cluster content themes using local LLM or embeddings
Relevance Scoring: Rank content based on:

- Historical engagement patterns
- Topic affinity scores
- Source authority weights
- Recency decay function



## Filtering System

- Interest Topics: Boost coefficient for specified domains/keywords
- Exclusion Rules: Hard filters for topics/sources/keywords
- Dynamic Learning: Optional implicit preference learning from interaction data

## Digest Generation

Format: Markdown/HTML with hierarchical topic organization. Later a voice version
Summarization: Optional LLM-powered abstracts for long-form content
Deduplication: Content fingerprinting to eliminate cross-source redundancy
Delivery: Local file generation, optional email/notification

## Technical Constraints

Best in class LLMs: use a grok fast model, currently grok-4-1-fast-reasoning
Extensible: Extendible architecture for new sources
Lightweight: Minimal resource footprint, scheduled batch processing

Success Metrics

Time to daily review < 10 minutes
Signal-to-noise ratio improvement (tracked via user feedback)

MVP Scope

Zotero API intergation first
Gmail then Twitter integration 
Basic keyword filtering
Daily markdown file output
Command-line configuration