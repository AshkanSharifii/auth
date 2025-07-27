import asyncio
import asyncpg
import uuid
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_super_admin():
    try:
        # Connect directly to database
        conn = await asyncpg.connect(
            "postgresql://postgres:Maziar17779@localhost:5432/PostinoAuthDB"
        )

        print("✅ Connected to database")

        # Get super_admin role ID
        role_query = "SELECT id FROM \"Role\" WHERE role_name = 'super_admin'"
        role_result = await conn.fetchrow(role_query)

        if not role_result:
            print("❌ Super admin role not found")
            await conn.close()
            return

        role_id = role_result['id']
        print(f"✅ Found super_admin role: {role_id}")

        # Check if admin already exists
        admin_check = "SELECT id FROM \"User\" WHERE email = 'admin@postino.com'"
        existing_admin = await conn.fetchrow(admin_check)

        if existing_admin:
            print("ℹ️ Super admin already exists!")
            print("📧 Email: admin@postino.com")
            print("🔒 Password: SuperAdmin123!")
            print("🔐 Authentication Methods:")
            print("   1. Email + Password")
            print("   2. Email + OTP")
            await conn.close()
            return

        # Hash password
        hashed_password = pwd_context.hash("SuperAdmin123!")

        # Create super admin user
        user_id = uuid.uuid4()
        insert_query = """
            INSERT INTO "User" (
                id, email, name, family, hashed_password, 
                position, personal_code, role_id, is_verified, 
                email_verified, phone_number_verified, is_active,
                phone_number
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """

        await conn.execute(
            insert_query,
            user_id,  # id
            "admin@postino.com",  # email (primary authentication)
            "Super",  # name
            "Admin",  # family
            hashed_password,  # hashed_password
            "Super Administrator",  # position
            "SA001",  # personal_code
            role_id,  # role_id
            True,  # is_verified
            True,  # email_verified
            False,  # phone_number_verified (no phone number)
            True,  # is_active
            None  # phone_number (optional)
        )

        print("🎉 Super admin created successfully!")
        print("📧 Email: admin@postino.com")
        print("🔒 Password: SuperAdmin123!")
        print("📱 Phone: Not provided (optional)")
        print("🆔 Personal Code: SA001")
        print()
        print("🔐 Available Authentication Methods:")
        print("   1. Email + Password Login:")
        print("      POST /auth/login")
        print("      { \"email\": \"admin@postino.com\", \"password\": \"SuperAdmin123!\" }")
        print()
        print("   2. Email + OTP Login:")
        print("      Step 1: POST /auth/otp/send")
        print("      { \"email\": \"admin@postino.com\" }")
        print("      Step 2: POST /auth/otp/verify")
        print("      { \"email\": \"admin@postino.com\", \"code\": \"1234\" }")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(create_super_admin())