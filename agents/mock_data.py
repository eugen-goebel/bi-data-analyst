"""
Mock data for --dry-run mode.

Provides a realistic InsightResult so the report can be generated
without an API key. The DataLoader, PatternAgent, and VisualizationAgent
run on real sample data even in dry-run mode.
"""

from .insight_agent import InsightResult, KeyFinding, Recommendation


MOCK_INSIGHTS = InsightResult(
    executive_summary=(
        "Analysis of 192 sales records across 4 regions and 4 product categories reveals "
        "strong overall growth driven by the Electronics segment, which shows a consistent "
        "upward trend of +48% over the 12-month period. However, the South region significantly "
        "underperforms with revenues 25% below the company average, representing a critical area "
        "for improvement. Q4 seasonal spikes and an anomalous returns event in the East region "
        "warrant immediate attention from management."
    ),
    key_findings=[
        KeyFinding(
            finding="Electronics category is the primary growth driver",
            evidence="Electronics revenue increased by approximately 48% from January to December, "
                     "outpacing all other categories significantly",
            business_implication="The company should consider increasing inventory allocation and "
                                "marketing budget for Electronics to capitalize on this momentum",
        ),
        KeyFinding(
            finding="South region consistently underperforms",
            evidence="South region generates approximately 25% less revenue than the company average "
                     "across all product categories",
            business_implication="Root cause analysis needed — potential issues include insufficient "
                                "sales coverage, competitive pressure, or demographic mismatch",
        ),
        KeyFinding(
            finding="Strong Q4 seasonal spike across all categories",
            evidence="Revenue increases by approximately 35% in Q4 (October-December) compared "
                     "to the annual average",
            business_implication="Inventory planning and staffing should account for this predictable "
                                "demand surge to avoid stockouts and delivery delays",
        ),
        KeyFinding(
            finding="Anomalous return rate in East region for Electronics",
            evidence="89 returns recorded for Electronics in the East region in July, compared to "
                     "a typical range of 5-15 returns per category per month",
            business_implication="Investigate potential product quality issue, shipping damage, or "
                                "fraudulent return activity specific to this region and period",
        ),
        KeyFinding(
            finding="Customer count strongly correlates with revenue",
            evidence="Pearson correlation of approximately 0.85 between customer_count and revenue",
            business_implication="Customer acquisition is the primary revenue lever — investing in "
                                "customer growth programs will likely have a direct revenue impact",
        ),
        KeyFinding(
            finding="Profit margins vary significantly by product category",
            evidence="Electronics and Home categories show higher profit margins (38-42%) compared "
                     "to Food (32-35%) and Clothing (35-38%)",
            business_implication="Product mix optimization toward higher-margin categories could "
                                "improve overall profitability without increasing revenue",
        ),
    ],
    recommendations=[
        Recommendation(
            title="Launch South Region Recovery Program",
            description="Conduct a comprehensive audit of the South region's sales operations, "
                        "competitive landscape, and customer demographics. Develop a targeted "
                        "action plan including potential territory redistribution and local marketing.",
            priority="High",
            category="Revenue Growth",
            expected_impact="Closing the 25% revenue gap could add an estimated 15-20% to overall company revenue",
        ),
        Recommendation(
            title="Investigate East Region Electronics Returns",
            description="Immediately audit the 89 Electronics returns from July in the East region. "
                        "Check for product defects, shipping damage patterns, or potential return fraud. "
                        "Implement enhanced quality checks if product issues are confirmed.",
            priority="High",
            category="Risk Mitigation",
            expected_impact="Resolving the root cause could save an estimated 5-8% in lost revenue and replacement costs",
        ),
        Recommendation(
            title="Increase Electronics Inventory for Q4",
            description="Given the 48% growth trend in Electronics combined with the 35% Q4 seasonal "
                        "spike, pre-position additional inventory starting in September. Consider "
                        "supplier negotiations for volume discounts.",
            priority="High",
            category="Operational Efficiency",
            expected_impact="Avoiding Q4 stockouts could capture an additional 10-12% revenue in the peak quarter",
        ),
        Recommendation(
            title="Implement Customer Acquisition Campaign",
            description="The strong correlation between customer count and revenue suggests that "
                        "a targeted customer acquisition campaign would directly drive revenue growth. "
                        "Focus on North and West regions where the conversion rate is already high.",
            priority="Medium",
            category="Revenue Growth",
            expected_impact="A 10% increase in customer count could drive approximately 8-10% revenue growth",
        ),
        Recommendation(
            title="Optimize Product Mix Toward Higher Margins",
            description="Shift promotional spend and shelf space allocation toward Electronics and Home "
                        "categories, which show 3-7 percentage points higher margins than Food and Clothing.",
            priority="Medium",
            category="Cost Reduction",
            expected_impact="A 5% shift in product mix could improve overall margin by 1-2 percentage points",
        ),
        Recommendation(
            title="Develop Predictive Demand Forecasting",
            description="The clear seasonal patterns and category trends suggest that implementing "
                        "a data-driven demand forecasting model would significantly improve inventory "
                        "management and reduce both overstock and stockout situations.",
            priority="Medium",
            category="Strategic",
            expected_impact="Improved forecasting could reduce inventory carrying costs by 10-15%",
        ),
    ],
    risk_alerts=[
        "South region revenue decline may accelerate without intervention — monitor monthly",
        "Electronics return anomaly in East could indicate a systemic quality control issue",
        "Heavy dependence on Q4 seasonal spike creates revenue concentration risk",
        "Rising cost ratios in Food category are compressing margins quarter over quarter",
        "Customer count growth rate is slowing in Q3, potentially signaling market saturation",
    ],
    opportunities=[
        "Electronics growth trajectory suggests potential for premium product line expansion",
        "North region overperformance could be replicated in other regions through best-practice sharing",
        "Cross-selling between high-traffic Food customers and higher-margin Electronics could boost basket size",
        "Seasonal data enables targeted pre-season marketing campaigns with predictable ROI",
        "Data quality score of 100% provides a strong foundation for advanced analytics and ML models",
    ],
    methodology_note=(
        "Analysis performed on 192 records spanning January–December 2025, covering 4 regions "
        "and 4 product categories. Statistical methods include trend detection via period-over-period "
        "comparison, Pearson correlation analysis, z-score outlier detection (threshold: 2.5), and "
        "monthly seasonality decomposition. Insights are generated using a multi-agent AI pipeline."
    ),
)
