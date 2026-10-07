import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


def generate_dbms_pdf(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=12)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, leading=18, spaceAfter=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=8)

    story = []

    # Page 1: Relational Model & Keys
    story.append(Paragraph("Database Management Systems: Foundations & Relational Model", title_style))
    story.append(Paragraph("Chapter 1: Relational Data Model and Key Constraints", h2_style))
    story.append(Paragraph(
        "A relational database organizes data into one or more tables (or relations) consisting of rows (tuples) and columns (attributes). "
        "Each table has a designated primary key that uniquely identifies each tuple within that table. "
        "A candidate key is a minimal superkey that can uniquely distinguish records. A primary key is chosen from candidate keys. "
        "Foreign keys establish referential integrity between tables, ensuring that values in the child table reference valid primary key tuples in the parent table.",
        body_style
    ))
    story.append(Paragraph(
        "Relational algebra forms the theoretical foundation of relational queries, comprising fundamental operations such as Selection (sigma), "
        "Projection (pi), Cartesian Product (cross), Union (cup), Difference (-), and Join (bowtie).",
        body_style
    ))
    story.append(PageBreak())

    # Page 2: Normalization
    story.append(Paragraph("Chapter 2: Database Normalization and Normal Forms", title_style))
    story.append(Paragraph("Understanding Normalization (1NF, 2NF, 3NF, BCNF)", h2_style))
    story.append(Paragraph(
        "Normalization is a systematic approach of decomposing tables to eliminate data redundancy and undesirable anomalies such as Insertion, "
        "Update, and Deletion anomalies. It organizes relational database fields and tables according to functional dependencies.",
        body_style
    ))
    story.append(Paragraph(
        "First Normal Form (1NF) mandates that table columns contain only atomic (indivisible) values and each row contains unique values with no repeating groups.\n\n"
        "Second Normal Form (2NF) requires that the table is in 1NF and all non-key attributes are fully functionally dependent on the entire primary key, eliminating partial dependencies.\n\n"
        "Third Normal Form (3NF) requires 2NF compliance and ensures that no non-prime attribute is transitively dependent on the primary key (X -> Y and Y -> Z where Z is non-prime). "
        "The benefits of 3NF include minimal storage redundancy, simplified data consistency, and prevention of anomalous modifications.\n\n"
        "Boyce-Codd Normal Form (BCNF) is a stricter version of 3NF where for every functional dependency X -> Y, X must be a super key.",
        body_style
    ))
    story.append(PageBreak())

    # Page 3: Transactions & ACID
    story.append(Paragraph("Chapter 3: Transaction Management & ACID Properties", title_style))
    story.append(Paragraph("ACID Guarantees and Concurrency Control", h2_style))
    story.append(Paragraph(
        "A transaction is a logical unit of database processing that includes one or more database access operations. "
        "To preserve database integrity, transactions must satisfy the four ACID properties: "
        "Atomicity (all or nothing execution), Consistency (database transitions from one valid state to another), "
        "Isolation (concurrent transactions execute independently without interference), and Durability (committed changes persist permanently even after hardware crashes).",
        body_style
    ))
    story.append(Paragraph(
        "Concurrency control techniques like Two-Phase Locking (2PL) and Timestamp Ordering ensure serializability and prevent dirty reads, unrepeatable reads, and phantom reads.",
        body_style
    ))

    doc.build(story)
    print(f"Generated: {output_path}")


def generate_networking_pdf(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=12)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, leading=18, spaceAfter=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=8)

    story = []

    # Page 1: Network Fundamentals
    story.append(Paragraph("Computer Networks & Communications: Architecture", title_style))
    story.append(Paragraph("Chapter 1: Network Fundamentals and Topologies", h2_style))
    story.append(Paragraph(
        "Computer networks interconnect autonomous computational devices for resource sharing and communication. "
        "Topologies describe how nodes are organized physically and logically: Star (central hub/switch), Bus (shared backbone cable), "
        "Ring (token circulation), Mesh (redundant point-to-point connections), and Hybrid. "
        "Packet switching divides data into discrete packets routed independently across routers using store-and-forward mechanisms.",
        body_style
    ))
    story.append(PageBreak())

    # Page 2: OSI Model
    story.append(Paragraph("Chapter 2: The OSI 7-Layer Reference Model", title_style))
    story.append(Paragraph("Detailed Architecture of the OSI Model", h2_style))
    story.append(Paragraph(
        "The Open Systems Interconnection (OSI) reference model is a conceptual framework standardized by ISO that partitions network communication into seven hierarchical layers:\n\n"
        "1. Physical Layer (Layer 1): Transmits raw unstructured bit streams over physical transmission media (cables, optical fibers, radio frequencies).\n\n"
        "2. Data Link Layer (Layer 2): Ensures node-to-node frame delivery, physical MAC addressing, framing, and error detection (Ethernet, Wi-Fi).\n\n"
        "3. Network Layer (Layer 3): Responsible for logical addressing (IP addresses), packet routing across multi-hop networks, and fragmentation.\n\n"
        "4. Transport Layer (Layer 4): Provides end-to-end process-to-process message transfer, port addressing, flow control, and reliability (TCP/UDP).\n\n"
        "5. Session Layer (Layer 5): Establishes, manages, synchronizes, and terminates communication sessions between cooperating applications.\n\n"
        "6. Presentation Layer (Layer 6): Translates, encrypts, and compresses data formats between the network and application (e.g., TLS, ASCII, JPEG).\n\n"
        "7. Application Layer (Layer 7): Provides network interfaces and protocols directly to end-user software applications (HTTP, DNS, SMTP, FTP).",
        body_style
    ))
    story.append(PageBreak())

    # Page 3: TCP vs UDP
    story.append(Paragraph("Chapter 3: Transport Layer Protocols: TCP vs UDP", title_style))
    story.append(Paragraph("Detailed Comparison Between TCP and UDP", h2_style))
    story.append(Paragraph(
        "The Transmission Control Protocol (TCP) and User Datagram Protocol (UDP) are the two core protocols of the Transport Layer.\n\n"
        "Differences between TCP and UDP:\n"
        "- Connection State: TCP is connection-oriented, requiring a 3-way handshake (SYN, SYN-ACK, ACK) prior to data transfer. UDP is connectionless and sends datagrams without establishing a handshake.\n"
        "- Reliability: TCP guarantees delivery through sequence numbers, acknowledgments (ACK), and retransmissions of lost packets. UDP provides best-effort delivery with no acknowledgment or automatic retransmission.\n"
        "- Ordering: TCP guarantees in-order packet delivery using sequence numbers. UDP packets may arrive out of order.\n"
        "- Overhead and Speed: TCP has a larger 20-byte header, congestion control, and flow control mechanisms, making it slower with higher overhead. UDP has a lightweight 8-byte header and low latency.\n"
        "- Use Cases: TCP is used where data accuracy is critical (HTTP/HTTPS, File Transfer FTP, SSH, email). UDP is used for real-time applications where low latency outweighs packet loss (VoIP, video streaming, DNS queries, online multiplayer games).",
        body_style
    ))

    doc.build(story)
    print(f"Generated: {output_path}")


def generate_cloud_pdf(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=12)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, leading=18, spaceAfter=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=8)

    story = []

    # Page 1: Cloud Concepts
    story.append(Paragraph("Cloud Computing: Architecture & Principles", title_style))
    story.append(Paragraph("Chapter 1: Definition and Advantages of Cloud Computing", h2_style))
    story.append(Paragraph(
        "Cloud computing is the on-demand delivery of IT resources (compute power, storage, databases, networking) via the Internet with pay-as-you-go pricing. "
        "According to NIST, essential cloud characteristics include on-demand self-service, broad network access, resource pooling, rapid elasticity, and measured service.",
        body_style
    ))
    story.append(Paragraph(
        "Key advantages of cloud computing include:\n"
        "- Cost Efficiency: Eliminates large capital expenditures (CapEx) for physical datacenters and hardware in favor of operational expenses (OpEx).\n"
        "- Elastic Scalability: Resources can dynamically scale up or down instantaneously in response to traffic spikes.\n"
        "- High Availability & Reliability: Redundant geographic zones provide fault tolerance and business continuity.\n"
        "- Rapid Global Deployment: Applications can be provisioned in multiple regions around the world within minutes.",
        body_style
    ))
    story.append(PageBreak())

    # Page 2: Service Models
    story.append(Paragraph("Chapter 2: Cloud Service Models (SPI Model)", title_style))
    story.append(Paragraph("Comparing IaaS, PaaS, and SaaS", h2_style))
    story.append(Paragraph(
        "Cloud services are categorized into three primary layers of abstraction:\n\n"
        "1. Infrastructure as a Service (IaaS): Provides fundamental computing resources including virtual machines, storage, and software-defined networks. The customer manages the operating system, middleware, and applications (e.g., AWS EC2, Google Compute Engine, Azure VMs).\n\n"
        "2. Platform as a Service (PaaS): Provides hardware and application development software platforms hosted by the cloud provider. Developers can focus on code deployment without managing underlying infrastructure (e.g., AWS Elastic Beanstalk, Heroku, Google App Engine).\n\n"
        "3. Software as a Service (SaaS): Delivers complete, ready-to-use software applications accessed over web browsers. The vendor handles all maintenance, infrastructure, and runtime (e.g., Google Workspace, Microsoft 365, Salesforce).",
        body_style
    ))

    doc.build(story)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_documents")
    os.makedirs(sample_dir, exist_ok=True)
    generate_dbms_pdf(os.path.join(sample_dir, "DBMS_Study_Notes.pdf"))
    generate_networking_pdf(os.path.join(sample_dir, "Computer_Networks_Guide.pdf"))
    generate_cloud_pdf(os.path.join(sample_dir, "Cloud_Computing_Essentials.pdf"))
    print("All sample academic PDFs created successfully.")
