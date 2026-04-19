"""Invoice information tools for the multi-agent system."""

import logging
from langchain_core.tools import tool
from src.db.database import run_query_safe

logger = logging.getLogger(__name__)


def _safe_int(value: str, label: str = "value") -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {label}: '{value}'. Please provide a numeric value.")


@tool
def get_invoices_by_customer_sorted_by_date(customer_id: str) -> str:
    """
    Look up all invoices for a customer using their ID.
    Returns invoices sorted by date (most recent first).
    """
    logger.info(f"TOOL_CALL: get_invoices_by_customer_sorted_by_date | customer_id={customer_id}")
    try:
        result = run_query_safe(
            """
            SELECT InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity,
                   BillingState, BillingCountry, BillingPostalCode, Total
            FROM Invoice
            WHERE CustomerId = :customer_id
            ORDER BY InvoiceDate DESC;
            """,
            {"customer_id": _safe_int(customer_id, "customer ID")},
        )
        logger.info(f"TOOL_RESULT: get_invoices_by_customer_sorted_by_date | result_length={len(result)}")
        if result == "[]":
            return f"No invoices found for customer {customer_id}."
        return result
    except Exception as e:
        logger.error(f"Error in get_invoices_by_customer_sorted_by_date: {e}")
        return f"Error retrieving invoices for customer {customer_id}. Please try again."


@tool
def get_invoice_line_items_sorted_by_price(customer_id: str) -> str:
    """
    Look up all purchased line items for a customer, sorted by unit price (highest first).
    Each row is a single purchased track (NOT a full invoice). An invoice with 5 tracks
    will appear as 5 separate rows, each showing the track name, unit price, and quantity.
    """
    logger.info(f"TOOL_CALL: get_invoice_line_items_sorted_by_price | customer_id={customer_id}")
    try:
        result = run_query_safe(
            """
            SELECT Invoice.InvoiceId, Invoice.InvoiceDate, Invoice.Total AS InvoiceTotal,
                   Track.Name AS TrackName, InvoiceLine.UnitPrice, InvoiceLine.Quantity
            FROM Invoice
            JOIN InvoiceLine ON Invoice.InvoiceId = InvoiceLine.InvoiceId
            JOIN Track ON InvoiceLine.TrackId = Track.TrackId
            WHERE Invoice.CustomerId = :customer_id
            ORDER BY InvoiceLine.UnitPrice DESC;
            """,
            {"customer_id": _safe_int(customer_id, "customer ID")},
        )
        logger.info(f"TOOL_RESULT: get_invoice_line_items_sorted_by_price | result_length={len(result)}")
        if result == "[]":
            return f"No purchase records found for customer {customer_id}."
        return result
    except Exception as e:
        logger.error(f"Error in get_invoice_line_items_sorted_by_price: {e}")
        return f"Error retrieving purchase records for customer {customer_id}. Please try again."


@tool
def get_employee_by_invoice_and_customer(invoice_id: str, customer_id: str) -> str:
    """
    Find the employee (support rep) associated with a specific invoice and customer.
    Returns employee full name, title, and email.
    """
    logger.info(f"TOOL_CALL: get_employee_by_invoice_and_customer | invoice_id={invoice_id}, customer_id={customer_id}")
    try:
        result = run_query_safe(
            """
            SELECT Employee.FirstName, Employee.LastName, Employee.Title, Employee.Email
            FROM Employee
            JOIN Customer ON Customer.SupportRepId = Employee.EmployeeId
            JOIN Invoice ON Invoice.CustomerId = Customer.CustomerId
            WHERE Invoice.InvoiceId = :invoice_id AND Invoice.CustomerId = :customer_id;
            """,
            {"invoice_id": _safe_int(invoice_id, "invoice ID"), "customer_id": _safe_int(customer_id, "customer ID")},
        )
        logger.info(f"TOOL_RESULT: get_employee_by_invoice_and_customer | result_length={len(result)}")
        if result == "[]":
            return f"No employee found for invoice ID {invoice_id} and customer ID {customer_id}."
        return result
    except Exception as e:
        logger.error(f"Error in get_employee_by_invoice_and_customer: {e}")
        return f"Error finding employee for invoice {invoice_id}. Please try again."


@tool
def get_invoice_line_items(invoice_id: str, customer_id: str) -> str:
    """
    Get the detailed line items (tracks purchased) for a specific invoice.
    Returns full track details for each purchased item.
    """
    logger.info(f"TOOL_CALL: get_invoice_line_items | invoice_id={invoice_id}, customer_id={customer_id}")
    try:
        result = run_query_safe(
            """
            SELECT Track.TrackId,
                   Track.Name AS TrackName,
                   Artist.Name AS ArtistName,
                   Album.Title AS AlbumTitle,
                   Genre.Name AS GenreName,
                   Track.Composer,
                   Track.Milliseconds,
                   ROUND(Track.Milliseconds / 60000.0, 1) AS DurationMinutes,
                   InvoiceLine.UnitPrice,
                   InvoiceLine.Quantity
            FROM InvoiceLine
            JOIN Invoice ON InvoiceLine.InvoiceId = Invoice.InvoiceId
            JOIN Track ON InvoiceLine.TrackId = Track.TrackId
            LEFT JOIN Album ON Track.AlbumId = Album.AlbumId
            LEFT JOIN Artist ON Album.ArtistId = Artist.ArtistId
            LEFT JOIN Genre ON Track.GenreId = Genre.GenreId
            WHERE Invoice.InvoiceId = :invoice_id AND Invoice.CustomerId = :customer_id
            ORDER BY Track.Name;
            """,
            {"invoice_id": _safe_int(invoice_id, "invoice ID"), "customer_id": _safe_int(customer_id, "customer ID")},
        )
        logger.info(f"TOOL_RESULT: get_invoice_line_items | result_length={len(result)}")
        if result == "[]":
            return f"No line items found for invoice {invoice_id} (customer {customer_id})."
        return result
    except Exception as e:
        logger.error(f"Error in get_invoice_line_items: {e}")
        return f"Error retrieving line items for invoice {invoice_id}. Please try again."


invoice_tools = [
    get_invoices_by_customer_sorted_by_date,
    get_invoice_line_items_sorted_by_price,
    get_employee_by_invoice_and_customer,
    get_invoice_line_items,
]
