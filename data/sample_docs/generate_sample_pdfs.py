"""
Generates realistic multi-page PDF documents for ApexGear Knowledge Base using ReportLab.
Domain: Consumer Electronics & E-Commerce Store (ApexGear)
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_pdf(filename: str, title: str, pages_content: list):
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=54, bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=8
    )

    story = []
    # Header title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))

    for page_idx, page_sections in enumerate(pages_content):
        if page_idx > 0:
            story.append(PageBreak())
            story.append(Paragraph(f"{title} (Continued)", title_style))
            story.append(Spacer(1, 10))

        for heading, paragraphs in page_sections:
            if heading:
                story.append(Paragraph(heading, heading_style))
            for para in paragraphs:
                story.append(Paragraph(para, body_style))
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated PDF: {filepath}")

def generate_all():
    # 1. Returns and Refunds Policy
    returns_content = [
        # Page 1
        [
            ("1. Standard 30-Day Return Policy", [
                "At ApexGear, customer satisfaction is our top priority. We accept returns of products purchased directly from our website within thirty (30) calendar days from the date of physical delivery.",
                "To qualify for a standard return, items must be in their original, undamaged packaging, include all original accessories, charging cables, user manuals, and warranty cards, and be in like-new cosmetic condition with no signs of customer misuse.",
                "Customers initiating a return for buyer's remorse (such as changing color preference or no longer needing the product) are responsible for return shipping costs of $6.99, which will be automatically deducted from the final refund amount."
            ]),
            ("2. Non-Returnable and Excluded Items", [
                "For hygiene and safety regulations, in-ear earphones (including ApexBuds and ApexBuds Pro) cannot be returned once the protective hygienic seal on the charging case has been opened or broken, unless verified to be defective under manufacturer warranty.",
                "Customized or personalized audio gear with custom laser engraving is non-refundable.",
                "Digital promotional cards, downloadable firmware keys, and clearance warehouse items marked as Final Sale are strictly non-returnable and non-refundable."
            ])
        ],
        # Page 2
        [
            ("3. Damaged or Defective Items Upon Delivery", [
                "If your shipment arrives physically damaged, cracked, or missing components, please contact ApexGear Customer Support within forty-eight (48) hours of package delivery.",
                "When reporting shipping damage, please provide your order confirmation number, photographic evidence showing the exterior shipping box and damaged item, and a description of the defect.",
                "ApexGear will provide an immediate prepaid return shipping label via email. Customers may choose between an expedited replacement unit shipped via next-day air at no extra charge or a 100% full refund to the original payment method."
            ]),
            ("4. Refund Processing Timelines and Delayed Refund Escalation", [
                "Once your returned package reaches our central fulfillment center in Columbus, Ohio, our quality assurance inspection team inspects and tests the device within two to three (2-3) business days.",
                "Approved refunds are automatically credited back to your original payment method. Depending on your financial institution, funds appear on your bank statement within five to seven (5-7) business days.",
                "ESCALATION PROTOCOL FOR DELAYED REFUNDS: If more than ten (10) business days have elapsed since our warehouse received your return tracking delivery and the refund has not posted to your account, the support agent must escalate the case immediately to Tier-2 Finance Support (Priority Ticket: BILLING-DELAY). The agent must verify the bank authorization code, issue a formal refund receipt to the customer, and credit the customer's ApexGear account with a $15 courtesy goodwill voucher for the inconvenience."
            ])
        ]
    ]

    create_pdf(
        "returns_and_refunds_policy.pdf",
        "ApexGear Returns, Refunds, and Replacement Policy",
        returns_content
    )

    # 2. Hardware Troubleshooting Guide
    troubleshooting_content = [
        # Page 1
        [
            ("1. ApexPro Wireless Headphones: Bluetooth Pairing and Factory Reset", [
                "If your ApexPro Wireless ANC Headphones fail to connect to your smartphone, laptop, or audio transmitter, perform a clean hardware factory reset.",
                "Factory Reset Procedure: Ensure the headphones are powered off. Press and hold down both the Power button and the Volume Down (-) button simultaneously for exactly ten (10) seconds. The LED status ring will rapidly flash purple three times and chime, indicating a complete reset. Delete 'ApexPro-BT' from your phone's Bluetooth memory and initiate a fresh scan.",
                "Dual Device Multipoint Connection: ApexPro headphones can connect to two devices simultaneously. If audio switches erratically between your laptop and phone, pause playback on the primary device for 3 seconds before starting media on the secondary device."
            ]),
            ("2. Battery Charging and Power Diagnostics", [
                "If your device will not power on or does not illuminate when connected to the charging cable, inspect the USB-C charging port for lint, dust, or moisture debris.",
                "Always use the supplied 5V/2A certified USB-C cable. High-voltage fast chargers exceeding 20W may trigger the built-in thermal protection fuse, temporarily halting charging for 30 minutes until the battery temperature normalizes.",
                "LED Battery Indicators: Solid Red indicates battery charging below 20%; Solid Amber indicates charging between 20% and 80%; Solid Green indicates 100% full charge. A blinking Red LED accompanied by a triple beep indicates battery critically depleted."
            ])
        ],
        # Page 2
        [
            ("3. Bluetooth Audio Latency, Stuttering, and Interference", [
                "If you experience audio cutouts, micro-stuttering, or high video-to-audio latency, ensure your device firmware is updated to version 2.4.1 or higher via the ApexGear Companion mobile app.",
                "Heavy 2.4 GHz WiFi router proximity, microwave ovens, or metal barriers can cause wireless packet dropouts. Maintain line-of-sight within thirty (30) feet (10 meters) of your host transmitter.",
                "Low Latency Gaming Mode: Triple-tap the Right Earbud or press the ANC toggle switch twice to activate Ultra-Low Latency Mode (45ms response time), optimized for mobile gaming and live video streaming."
            ]),
            ("4. Water Resistance and Warranty Exclusions", [
                "ApexGear sports earbuds and headphones feature an IPX4 splash-resistance rating. They are certified to resist sweat during intense exercise and light raindrops.",
                "IPX4 is NOT waterproof. Do not submerge the headphones in water, wear them while swimming, or rinse them under running tap water.",
                "Liquid submersion voids the standard hardware warranty. If sweat enters the speaker mesh, gently pat dry with a microfiber cloth and let air-dry in a well-ventilated room for 24 hours before charging."
            ])
        ]
    ]

    create_pdf(
        "hardware_troubleshooting_guide.pdf",
        "ApexGear Technical Support and Hardware Troubleshooting Guide",
        troubleshooting_content
    )

    # 3. Shipping and Delivery Policy
    shipping_content = [
        # Page 1
        [
            ("1. Shipping Methods, Costs, and Delivery Times", [
                "ApexGear ships orders Monday through Friday from our central warehouse. Orders placed before 1:00 PM Eastern Time are processed and dispatched on the same business day.",
                "Standard Shipping ($4.99 or Free on orders above $50): Delivered within 3 to 5 business days via USPS or FedEx Ground.",
                "Express Priority Shipping ($14.99): Delivered within 1 to 2 business days via FedEx 2Day Air.",
                "International Shipping ($24.99): Delivered within 7 to 14 business days via DHL Express. International customers are responsible for local customs duties and VAT taxes assessed at destination customs."
            ]),
            ("2. Order Tracking and Carrier Scans", [
                "Once your order has been packaged and handed over to the carrier, an automated email and SMS notification containing your 12-digit tracking number is dispatched.",
                "Please allow up to twenty-four (24) to forty-eight (48) hours for initial tracking scans to appear on the carrier tracking portal, as packages are scanned at regional sorting hubs.",
                "If your tracking status shows 'Label Created' or 'In Transit' with no scan update for more than 4 business days, contact ApexGear Support to initiate a carrier trace."
            ])
        ],
        # Page 2
        [
            ("3. Lost Shipments, Stolen Packages, and Signature Requirements", [
                "Packages marked as 'Delivered' by the courier but not found by the recipient: Check side doors, porches, parcel lockers, and inquire with neighbors or building leasing offices.",
                "If the package remains missing forty-eight (48) hours after marked delivery, ApexGear will file an official Lost In Transit Claim with the postal courier.",
                "High-Value Orders: All orders containing products valued at $200 or more automatically require a direct adult signature upon delivery to prevent porch piracy.",
                "If a lost package claim is verified by the carrier investigation (typically completed within 3 business days), ApexGear will immediately dispatch a replacement shipment or issue a full refund."
            ]),
            ("4. Modifying Shipping Addresses and Order Cancellations", [
                "Due to automated high-speed warehouse fulfillment, shipping addresses can only be changed within two (2) hours of placing the order.",
                "To modify an address or cancel an accidental order, contact Live Support immediately or use the 'Cancel Order' button in your customer account dashboard.",
                "Once an order enters the 'Fulfillment Processing' stage, warehouse staff cannot intercept the shipment. Customers must wait for package receipt and use our prepaid return portal."
            ])
        ]
    ]

    create_pdf(
        "shipping_and_delivery_policy.pdf",
        "ApexGear Shipping, Tracking, and Fulfillment Guidelines",
        shipping_content
    )

    # 4. Billing, Warranty, and Account FAQ
    billing_content = [
        # Page 1
        [
            ("1. Billing Inquiries, Double Charges, and Authorization Holds", [
                "When you place an order on ApexGear.com, an electronic pre-authorization hold is placed on your credit or debit card for the order total. Your card is only finalized and charged when the package is shipped.",
                "If you see two identical pending transactions on your online banking statement after an order attempt that showed an error, one is an authorization hold that will drop off automatically within three to five (3-5) business days depending on your bank.",
                "BILLING DISPUTE ESCALATION: If duplicate completed charges appear on your bank statement (not pending holds), the customer service agent must verify the charge transaction IDs, escalate to the Billing Specialist Team, and process an immediate refund of the duplicate amount within 24 hours."
            ]),
            ("2. Accepted Payment Methods and Security", [
                "ApexGear accepts Visa, MasterCard, American Express, Discover, PayPal, Apple Pay, Google Pay, and ApexGear Digital Gift Cards.",
                "We do not accept cash-on-delivery (COD), personal checks, direct wire transfers, or cryptocurrency payments.",
                "All online checkout transactions are encrypted with 256-bit TLS encryption and comply with PCI-DSS Level 1 security standards."
            ])
        ],
        # Page 2
        [
            ("3. One-Year Limited Manufacturer Warranty", [
                "All new ApexGear hardware products include a complimentary one (1) year limited manufacturer warranty against defects in materials and workmanship, effective from the date of original purchase.",
                "Warranty Coverage Includes: Internal speaker driver failure, Bluetooth chip failure, microphone malfunction, and charging circuitry defects occurring during normal recommended usage.",
                "Warranty Exclusions: Accidental drops, shattered plastic housings, liquid or water submersion, modifications made by unauthorized repair shops, and loss or theft of the item.",
                "Filing a Warranty Claim: To submit a warranty claim, visit apexgear.com/warranty with your serial number, proof of purchase invoice, and description of the defect. Approved warranty claims receive a factory-certified replacement unit."
            ]),
            ("4. 14-Day Price Adjustment Guarantee", [
                "If ApexGear reduces the price of an item you purchased within fourteen (14) days of your delivery date, we will gladly refund the price difference.",
                "To request a price match, contact Customer Support with your order number and the live active sale listing. Price adjustments apply to official ApexGear sales only and exclude third-party marketplace sellers."
            ])
        ]
    ]

    create_pdf(
        "billing_and_warranty_faq.pdf",
        "ApexGear Billing, Payment, and Warranty FAQ",
        billing_content
    )

if __name__ == "__main__":
    generate_all()
