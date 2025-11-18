#!/usr/bin/env python3
"""
AI Earnings Call Sentiment Analyzer
====================================

Advanced NLP-based sentiment analysis for earnings call transcripts.

Features:
- Management tone analysis (confident vs defensive)
- Guidance change detection
- Question evasion pattern recognition
- Sentiment divergence (prepared remarks vs Q&A)
- Key phrase frequency analysis
- Comparative analysis across quarters
- Risk language detection

Usage:
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_transcript(transcript)
    score = result['composite_score']
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter
import numpy as np

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Advanced sentiment analyzer for earnings call transcripts.

    Uses multiple NLP techniques:
    - Lexicon-based sentiment scoring
    - Pattern matching for management behavior
    - Frequency analysis for key phrases
    - Comparative analysis across time periods
    """

    def __init__(self):
        """Initialize sentiment analyzer with dictionaries and patterns."""

        # Bullish/confident language
        self.bullish_words = {
            'exceed', 'exceeded', 'exceeding', 'outperform', 'outperformed',
            'strong', 'robust', 'solid', 'healthy', 'impressive',
            'growth', 'growing', 'expand', 'expanding', 'expansion',
            'record', 'milestone', 'breakthrough', 'success', 'successful',
            'confidence', 'confident', 'optimistic', 'positive', 'encouraged',
            'opportunity', 'opportunities', 'momentum', 'accelerating',
            'improve', 'improved', 'improving', 'improvement', 'better',
            'increase', 'increased', 'increasing', 'gain', 'gained',
            'leader', 'leadership', 'innovation', 'innovative'
        }

        # Bearish/cautious language
        self.bearish_words = {
            'headwind', 'headwinds', 'challenge', 'challenges', 'challenging',
            'pressure', 'pressures', 'difficult', 'difficulty', 'concern',
            'concerned', 'uncertainty', 'uncertain', 'cautious', 'volatile',
            'volatility', 'weak', 'weakness', 'soft', 'softness', 'decline',
            'declined', 'declining', 'decrease', 'decreased', 'decreasing',
            'miss', 'missed', 'below', 'short', 'shortfall', 'disappointing',
            'struggle', 'struggling', 'delay', 'delayed', 'postpone', 'postponed',
            'risk', 'risks', 'threat', 'threats', 'adverse', 'unfavorable',
            'competitive', 'competition', 'disruption', 'disrupted'
        }

        # Guidance language
        self.guidance_raising = {
            'raising', 'increase', 'increased', 'raising guidance',
            'increase guidance', 'above', 'higher than', 'upward revision',
            'upgrade', 'upgraded', 'improving outlook'
        }

        self.guidance_lowering = {
            'lowering', 'lower', 'reduced', 'reducing', 'lowering guidance',
            'lower guidance', 'below', 'downward revision', 'downgrade',
            'cutting', 'cut guidance'
        }

        # Evasive language patterns
        self.evasive_patterns = [
            r"we'll get back to you on that",
            r"don't have that number in front of me",
            r"can't comment on that",
            r"not prepared to discuss",
            r"too early to tell",
            r"difficult to quantify",
            r"hard to say",
            r"various factors",
            r"it's complicated",
            r"depends on many things"
        ]

        # Risk-related phrases
        self.risk_phrases = {
            'macro uncertainty', 'economic uncertainty', 'market uncertainty',
            'geopolitical risk', 'regulatory risk', 'supply chain',
            'inflation', 'interest rate', 'recession', 'slowdown',
            'credit conditions', 'liquidity', 'cash flow'
        }

    def analyze_transcript(self, transcript: Dict) -> Dict:
        """
        Perform comprehensive sentiment analysis on a transcript.

        Args:
            transcript: Dictionary with 'content', 'ticker', 'date', etc.

        Returns:
            Analysis results dictionary with scores and metrics
        """
        content = transcript.get('content', '')

        if not content:
            logger.warning(f"Empty transcript for {transcript.get('ticker', 'unknown')}")
            return self._empty_result()

        # Split into sections
        sections = self._split_transcript(content)

        # Analyze each section
        prepared_remarks = sections.get('prepared_remarks', '')
        qa_section = sections.get('qa', '')

        # Calculate various metrics
        results = {
            'ticker': transcript.get('ticker', ''),
            'date': transcript.get('date', ''),
            'quarter': transcript.get('quarter', ''),
            'year': transcript.get('year', ''),

            # Overall sentiment
            'composite_score': 0.0,  # -100 (very bearish) to +100 (very bullish)

            # Section-specific scores
            'prepared_remarks_score': 0.0,
            'qa_score': 0.0,
            'sentiment_divergence': 0.0,  # Difference between prepared and Q&A

            # Specific indicators
            'bullish_word_count': 0,
            'bearish_word_count': 0,
            'guidance_signal': 0,  # -1 lowering, 0 neutral, +1 raising
            'evasion_count': 0,
            'risk_mention_count': 0,

            # Confidence metrics
            'management_confidence': 0.0,  # 0-100 scale
            'tone_shift': 0.0,  # Positive = more confident, negative = less confident

            # Key phrases
            'top_bullish_phrases': [],
            'top_bearish_phrases': [],
            'key_risks_mentioned': [],

            # Metadata
            'transcript_length': len(content),
            'word_count': len(content.split()),
            'analysis_timestamp': datetime.now().isoformat()
        }

        # Perform analyses
        results.update(self._analyze_sentiment(content))
        results.update(self._analyze_guidance(content))
        results.update(self._analyze_evasion(qa_section))
        results.update(self._analyze_risks(content))
        results.update(self._calculate_confidence(prepared_remarks, qa_section))

        # Calculate composite score
        results['composite_score'] = self._calculate_composite_score(results)

        return results

    def analyze_multiple_transcripts(
        self,
        transcripts: List[Dict]
    ) -> Dict:
        """
        Analyze multiple transcripts and identify trends.

        Args:
            transcripts: List of transcript dictionaries (newest first)

        Returns:
            Comparative analysis with trend detection
        """
        if not transcripts:
            return {'error': 'No transcripts provided'}

        # Analyze each individually
        analyses = [self.analyze_transcript(t) for t in transcripts]

        # Sort by date (newest first)
        analyses.sort(key=lambda x: x.get('date', ''), reverse=True)

        # Calculate trends
        trend_analysis = {
            'ticker': analyses[0].get('ticker', ''),
            'num_transcripts': len(analyses),
            'date_range': f"{analyses[-1].get('date', '')} to {analyses[0].get('date', '')}",

            # Individual results
            'transcript_analyses': analyses,

            # Trend metrics
            'sentiment_trend': self._calculate_trend([a['composite_score'] for a in analyses]),
            'confidence_trend': self._calculate_trend([a['management_confidence'] for a in analyses]),
            'risk_mention_trend': self._calculate_trend([a['risk_mention_count'] for a in analyses]),

            # Change indicators
            'sentiment_change': 0.0,  # Latest vs previous
            'confidence_change': 0.0,
            'guidance_consistency': True,  # Are they changing guidance direction?

            # Red flags
            'red_flags': [],
            'green_flags': [],

            # Overall assessment
            'overall_signal': 'neutral',  # 'bullish', 'neutral', 'bearish'
            'signal_strength': 0.0,  # 0-100 confidence in signal
        }

        # Calculate changes
        if len(analyses) >= 2:
            latest = analyses[0]
            previous = analyses[1]

            trend_analysis['sentiment_change'] = latest['composite_score'] - previous['composite_score']
            trend_analysis['confidence_change'] = latest['management_confidence'] - previous['management_confidence']

            # Detect red/green flags
            trend_analysis['red_flags'] = self._detect_red_flags(analyses)
            trend_analysis['green_flags'] = self._detect_green_flags(analyses)

            # Overall signal
            trend_analysis['overall_signal'] = self._determine_overall_signal(trend_analysis)
            trend_analysis['signal_strength'] = self._calculate_signal_strength(trend_analysis)

        return trend_analysis

    def _split_transcript(self, content: str) -> Dict[str, str]:
        """Split transcript into prepared remarks and Q&A sections."""
        sections = {}

        # Try to find Q&A section
        qa_markers = [
            r'Q&A|Q & A|Question.*Answer|Operator.*Question',
            r'question.*session|questions.*answers',
        ]

        qa_start = -1
        for pattern in qa_markers:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                qa_start = match.start()
                break

        if qa_start > 0:
            sections['prepared_remarks'] = content[:qa_start]
            sections['qa'] = content[qa_start:]
        else:
            # No clear Q&A section found
            sections['prepared_remarks'] = content
            sections['qa'] = ''

        return sections

    def _analyze_sentiment(self, content: str) -> Dict:
        """Analyze overall sentiment using lexicon-based approach."""
        words = re.findall(r'\b\w+\b', content.lower())

        bullish_count = sum(1 for word in words if word in self.bullish_words)
        bearish_count = sum(1 for word in words if word in self.bearish_words)

        total_sentiment_words = bullish_count + bearish_count
        if total_sentiment_words == 0:
            sentiment_ratio = 0
        else:
            sentiment_ratio = (bullish_count - bearish_count) / total_sentiment_words

        return {
            'bullish_word_count': bullish_count,
            'bearish_word_count': bearish_count,
            'sentiment_ratio': sentiment_ratio
        }

    def _analyze_guidance(self, content: str) -> Dict:
        """Detect guidance changes."""
        lower_content = content.lower()

        raising_signals = sum(1 for phrase in self.guidance_raising if phrase in lower_content)
        lowering_signals = sum(1 for phrase in self.guidance_lowering if phrase in lower_content)

        if raising_signals > lowering_signals:
            guidance_signal = 1
        elif lowering_signals > raising_signals:
            guidance_signal = -1
        else:
            guidance_signal = 0

        return {
            'guidance_signal': guidance_signal,
            'guidance_raising_mentions': raising_signals,
            'guidance_lowering_mentions': lowering_signals
        }

    def _analyze_evasion(self, qa_section: str) -> Dict:
        """Detect evasive answers in Q&A."""
        if not qa_section:
            return {'evasion_count': 0, 'evasion_rate': 0.0}

        evasion_count = 0
        for pattern in self.evasive_patterns:
            matches = re.findall(pattern, qa_section, re.IGNORECASE)
            evasion_count += len(matches)

        # Estimate number of questions
        question_count = len(re.findall(r'analyst:|question:', qa_section, re.IGNORECASE))
        if question_count == 0:
            question_count = 1

        evasion_rate = evasion_count / question_count

        return {
            'evasion_count': evasion_count,
            'evasion_rate': evasion_rate
        }

    def _analyze_risks(self, content: str) -> Dict:
        """Identify risk mentions."""
        lower_content = content.lower()

        risk_mentions = []
        for phrase in self.risk_phrases:
            if phrase in lower_content:
                count = lower_content.count(phrase)
                risk_mentions.append({
                    'phrase': phrase,
                    'count': count
                })

        risk_mentions.sort(key=lambda x: x['count'], reverse=True)

        return {
            'risk_mention_count': len(risk_mentions),
            'key_risks_mentioned': [r['phrase'] for r in risk_mentions[:5]],
            'total_risk_occurrences': sum(r['count'] for r in risk_mentions)
        }

    def _calculate_confidence(self, prepared: str, qa: str) -> Dict:
        """Calculate management confidence score."""

        # Prepared remarks sentiment
        prepared_words = re.findall(r'\b\w+\b', prepared.lower())
        prep_bullish = sum(1 for w in prepared_words if w in self.bullish_words)
        prep_bearish = sum(1 for w in prepared_words if w in self.bearish_words)

        # Q&A sentiment
        qa_words = re.findall(r'\b\w+\b', qa.lower())
        qa_bullish = sum(1 for w in qa_words if w in self.bullish_words)
        qa_bearish = sum(1 for w in qa_words if w in self.bearish_words)

        # Calculate scores (0-100 scale)
        if len(prepared_words) > 0:
            prep_score = 50 + ((prep_bullish - prep_bearish) / len(prepared_words)) * 500
        else:
            prep_score = 50

        if len(qa_words) > 0:
            qa_score = 50 + ((qa_bullish - qa_bearish) / len(qa_words)) * 500
        else:
            qa_score = 50

        # Clamp to 0-100
        prep_score = max(0, min(100, prep_score))
        qa_score = max(0, min(100, qa_score))

        return {
            'prepared_remarks_score': round(prep_score, 2),
            'qa_score': round(qa_score, 2),
            'sentiment_divergence': round(prep_score - qa_score, 2),
            'management_confidence': round((prep_score + qa_score) / 2, 2)
        }

    def _calculate_composite_score(self, results: Dict) -> float:
        """
        Calculate overall composite sentiment score.

        Range: -100 (very bearish) to +100 (very bullish)
        """
        # Weight different factors
        weights = {
            'sentiment_ratio': 30,
            'guidance_signal': 25,
            'management_confidence': 20,
            'evasion_penalty': -15,
            'risk_penalty': -10
        }

        score = 0.0

        # Sentiment ratio contribution
        score += results.get('sentiment_ratio', 0) * weights['sentiment_ratio']

        # Guidance signal contribution
        score += results.get('guidance_signal', 0) * weights['guidance_signal']

        # Management confidence (convert from 0-100 to -1 to +1)
        confidence_normalized = (results.get('management_confidence', 50) - 50) / 50
        score += confidence_normalized * weights['management_confidence']

        # Evasion penalty
        evasion_rate = results.get('evasion_rate', 0)
        score += evasion_rate * weights['evasion_penalty']

        # Risk mention penalty
        risk_count = results.get('risk_mention_count', 0)
        risk_penalty = min(risk_count / 10, 1.0)  # Cap at 10 risks
        score += risk_penalty * weights['risk_penalty']

        # Clamp to -100 to +100
        score = max(-100, min(100, score))

        return round(score, 2)

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return 'insufficient_data'

        # Simple linear trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 5:
            return 'improving'
        elif slope < -5:
            return 'deteriorating'
        else:
            return 'stable'

    def _detect_red_flags(self, analyses: List[Dict]) -> List[str]:
        """Detect warning signs from transcript analysis."""
        flags = []

        if len(analyses) < 2:
            return flags

        latest = analyses[0]
        previous = analyses[1]

        # Sentiment deterioration
        if latest['composite_score'] < previous['composite_score'] - 20:
            flags.append("Significant sentiment deterioration")

        # Confidence drop
        if latest['management_confidence'] < previous['management_confidence'] - 15:
            flags.append("Management confidence declining")

        # Increasing evasion
        if latest['evasion_count'] > previous['evasion_count'] * 1.5:
            flags.append("Increased evasive responses in Q&A")

        # Guidance lowering
        if latest['guidance_signal'] == -1:
            flags.append("Guidance lowered")

        # Risk mentions increasing
        if latest['risk_mention_count'] > previous['risk_mention_count'] * 1.5:
            flags.append("Risk mentions increasing")

        # Large divergence between prepared and Q&A
        if abs(latest['sentiment_divergence']) > 20:
            flags.append("Large sentiment gap between prepared remarks and Q&A")

        return flags

    def _detect_green_flags(self, analyses: List[Dict]) -> List[str]:
        """Detect positive signs from transcript analysis."""
        flags = []

        if len(analyses) < 2:
            return flags

        latest = analyses[0]
        previous = analyses[1]

        # Sentiment improvement
        if latest['composite_score'] > previous['composite_score'] + 20:
            flags.append("Significant sentiment improvement")

        # Confidence increase
        if latest['management_confidence'] > previous['management_confidence'] + 15:
            flags.append("Management confidence increasing")

        # Guidance raising
        if latest['guidance_signal'] == 1:
            flags.append("Guidance raised")

        # Low evasion
        if latest['evasion_count'] < 2:
            flags.append("Direct and transparent Q&A responses")

        # Consistent positive sentiment
        if all(a['composite_score'] > 30 for a in analyses[:3]):
            flags.append("Consistently positive sentiment across quarters")

        return flags

    def _determine_overall_signal(self, trend_analysis: Dict) -> str:
        """Determine overall trading signal based on trend analysis."""
        sentiment_change = trend_analysis.get('sentiment_change', 0)
        red_flags = len(trend_analysis.get('red_flags', []))
        green_flags = len(trend_analysis.get('green_flags', []))

        # Strong bearish signal
        if red_flags >= 3 or sentiment_change < -30:
            return 'bearish'

        # Strong bullish signal
        if green_flags >= 3 or sentiment_change > 30:
            return 'bullish'

        # Moderate signals
        if red_flags > green_flags and sentiment_change < -10:
            return 'bearish'

        if green_flags > red_flags and sentiment_change > 10:
            return 'bullish'

        return 'neutral'

    def _calculate_signal_strength(self, trend_analysis: Dict) -> float:
        """Calculate confidence in the overall signal (0-100)."""
        num_transcripts = trend_analysis.get('num_transcripts', 0)
        red_flags = len(trend_analysis.get('red_flags', []))
        green_flags = len(trend_analysis.get('green_flags', []))
        sentiment_change = abs(trend_analysis.get('sentiment_change', 0))

        # More transcripts = higher confidence
        data_confidence = min(num_transcripts * 20, 40)

        # Clear flags = higher confidence
        flag_confidence = max(red_flags, green_flags) * 15

        # Large sentiment change = higher confidence
        change_confidence = min(sentiment_change / 2, 30)

        total = data_confidence + flag_confidence + change_confidence

        return round(min(total, 100), 2)

    def _empty_result(self) -> Dict:
        """Return empty analysis result."""
        return {
            'composite_score': 0.0,
            'error': 'Empty or invalid transcript'
        }


# Testing and examples
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from transcript_fetcher import MockTranscriptGenerator

    print("=" * 80)
    print("SENTIMENT ANALYZER TEST")
    print("=" * 80)

    # Generate mock transcripts with different sentiments
    mock_gen = MockTranscriptGenerator()
    analyzer = SentimentAnalyzer()

    # Test 1: Single transcript analysis
    print("\n" + "=" * 80)
    print("TEST 1: Single Transcript Analysis")
    print("=" * 80)

    for sentiment in ['bullish', 'neutral', 'bearish']:
        print(f"\n--- {sentiment.upper()} Transcript ---")
        transcript = mock_gen.generate_transcript('AAPL', 'Q4', 2024, sentiment)
        result = analyzer.analyze_transcript(transcript)

        print(f"Composite Score: {result['composite_score']:.2f}")
        print(f"Management Confidence: {result['management_confidence']:.2f}")
        print(f"Guidance Signal: {result['guidance_signal']}")
        print(f"Bullish Words: {result['bullish_word_count']}, Bearish Words: {result['bearish_word_count']}")
        print(f"Evasion Count: {result['evasion_count']}")

    # Test 2: Multi-transcript trend analysis
    print("\n" + "=" * 80)
    print("TEST 2: Multi-Transcript Trend Analysis")
    print("=" * 80)

    transcripts = mock_gen.generate_comparison_transcripts('NVDA', num_quarters=3)
    trend_result = analyzer.analyze_multiple_transcripts(transcripts)

    print(f"\nTicker: {trend_result['ticker']}")
    print(f"Transcripts Analyzed: {trend_result['num_transcripts']}")
    print(f"Date Range: {trend_result['date_range']}")
    print(f"\nSentiment Trend: {trend_result['sentiment_trend']}")
    print(f"Confidence Trend: {trend_result['confidence_trend']}")
    print(f"Sentiment Change (latest vs previous): {trend_result['sentiment_change']:.2f}")
    print(f"\nOverall Signal: {trend_result['overall_signal'].upper()}")
    print(f"Signal Strength: {trend_result['signal_strength']:.1f}%")

    print(f"\nRed Flags ({len(trend_result['red_flags'])}):")
    for flag in trend_result['red_flags']:
        print(f"  ⚠️  {flag}")

    print(f"\nGreen Flags ({len(trend_result['green_flags'])}):")
    for flag in trend_result['green_flags']:
        print(f"  ✅ {flag}")

    print("\n" + "=" * 80)
    print("Individual Transcript Scores:")
    print("=" * 80)
    for i, analysis in enumerate(trend_result['transcript_analyses']):
        print(f"{i+1}. {analysis['quarter']} {analysis['year']}: Score = {analysis['composite_score']:.1f}, "
              f"Confidence = {analysis['management_confidence']:.1f}")
