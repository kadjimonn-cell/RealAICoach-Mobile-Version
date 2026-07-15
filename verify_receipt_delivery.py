"""
Verify receipt delivery flags and recovery queue for PayPal orders
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "realaicoach")

ORDER_IDS = [
    "1UW49833CW014203Y",  # Basic
    "7WR35562CP5880350",  # Premium
]

async def check_receipt_delivery():
    """Check receipt delivery flags in payment records"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 80)
    print("RECEIPT DELIVERY FLAGS & RECOVERY QUEUE VERIFICATION")
    print("=" * 80)
    
    # Check payment records
    print("\n=== PAYMENT RECORDS ===")
    for order_id in ORDER_IDS:
        payment = await db.payments.find_one(
            {"$or": [{"payment_id": order_id}, {"session_id": order_id}]},
            {"_id": 0}
        )
        
        if payment:
            print(f"\n✅ Order {order_id} found in payments collection:")
            print(f"   payment_id: {payment.get('payment_id')}")
            print(f"   status: {payment.get('status')}")
            print(f"   user_receipt_sent: {payment.get('user_receipt_sent', False)}")
            print(f"   admin_receipt_sent: {payment.get('admin_receipt_sent', False)}")
            print(f"   receipt_delivery_ok: {payment.get('receipt_delivery_ok', False)}")
            print(f"   notification_sent: {payment.get('notification_sent', False)}")
            print(f"   created_at: {payment.get('created_at')}")
        else:
            print(f"\n❌ Order {order_id} NOT found in payments collection")
    
    # Check payment transactions
    print("\n=== PAYMENT TRANSACTIONS ===")
    for order_id in ORDER_IDS:
        tx = await db.payment_transactions.find_one(
            {"$or": [{"session_id": order_id}, {"transaction_id": order_id}]},
            {"_id": 0}
        )
        
        if tx:
            print(f"\n✅ Order {order_id} found in payment_transactions:")
            print(f"   transaction_id: {tx.get('transaction_id')}")
            print(f"   session_id: {tx.get('session_id')}")
            print(f"   payment_status: {tx.get('payment_status')}")
            print(f"   notification_sent: {tx.get('notification_sent', False)}")
            print(f"   user_receipt_sent: {tx.get('user_receipt_sent', False)}")
            print(f"   admin_receipt_sent: {tx.get('admin_receipt_sent', False)}")
            print(f"   receipt_delivery_ok: {tx.get('receipt_delivery_ok', False)}")
        else:
            print(f"\n❌ Order {order_id} NOT found in payment_transactions")
    
    # Check recovery queue
    print("\n=== RECOVERY QUEUE ===")
    recovery_count = await db.payment_notification_recovery.count_documents({})
    print(f"Total entries in recovery queue: {recovery_count}")
    
    if recovery_count > 0:
        print("\n⚠️  Recovery queue entries found:")
        async for entry in db.payment_notification_recovery.find({}, {"_id": 0}).limit(10):
            print(f"   - {entry.get('payment_id')} | {entry.get('reason')} | {entry.get('created_at')}")
    else:
        print("✅ Recovery queue is empty (no failed notifications)")
    
    # Check for our specific orders in recovery queue
    for order_id in ORDER_IDS:
        recovery = await db.payment_notification_recovery.find_one(
            {"$or": [{"payment_id": order_id}, {"session_id": order_id}]},
            {"_id": 0}
        )
        
        if recovery:
            print(f"\n❌ Order {order_id} found in recovery queue:")
            print(f"   reason: {recovery.get('reason')}")
            print(f"   retry_count: {recovery.get('retry_count', 0)}")
            print(f"   created_at: {recovery.get('created_at')}")
        else:
            print(f"\n✅ Order {order_id} NOT in recovery queue")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Check if all flags are set
    all_flags_ok = True
    for order_id in ORDER_IDS:
        payment = await db.payments.find_one(
            {"$or": [{"payment_id": order_id}, {"session_id": order_id}]},
            {"_id": 0, "user_receipt_sent": 1, "admin_receipt_sent": 1, "receipt_delivery_ok": 1}
        )
        
        if payment:
            flags_ok = (
                payment.get('user_receipt_sent', False) and
                payment.get('admin_receipt_sent', False) and
                payment.get('receipt_delivery_ok', False)
            )
            if not flags_ok:
                all_flags_ok = False
                print(f"⚠️  Order {order_id}: Receipt delivery flags NOT all true")
        else:
            all_flags_ok = False
            print(f"❌ Order {order_id}: Payment record not found")
    
    if all_flags_ok:
        print("✅ All receipt delivery flags are TRUE for both orders")
    
    if recovery_count == 0:
        print("✅ Recovery queue is EMPTY (no failed notifications)")
    else:
        print(f"⚠️  Recovery queue has {recovery_count} entries")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_receipt_delivery())
