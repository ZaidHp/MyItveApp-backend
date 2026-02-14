from app.core.database import get_database

db = get_database()
admins_collection = db['Admins']
students_collection = db['Students']
schools_collection = db['Schools']
promoters_collection = db['Promoters']

async def get_user_counts() -> dict:
    """
    Fetch the count of users for each role and the total.
    """
    admins = await admins_collection.count_documents({})
    students = await students_collection.count_documents({})
    schools = await schools_collection.count_documents({})
    promoters = await promoters_collection.count_documents({})
    
    total_users = admins + students + schools + promoters
    
    return {
        "total_users": total_users,
        "admins": admins,
        "students": students,
        "schools_colleges": schools,
        "promoters": promoters
    }

async def get_all_users_list() -> dict:
    """
    Fetch all users from all collections, excluding sensitive data like passwords.
    """
    all_users = []

    # Helper function to fetch and format users
    async def fetch_from_collection(collection):
        # Fetch users excluding the password field
        users = await collection.find({}, {"password": 0}).to_list(length=100)
        # Convert ObjectId to string for JSON serialization
        for user in users:
            user['_id'] = str(user['_id'])
        return users

    # Gather data from all collections
    # Note: For very large datasets, you might want to implement pagination here
    admins = await fetch_from_collection(admins_collection)
    students = await fetch_from_collection(students_collection)
    schools = await fetch_from_collection(schools_collection)
    promoters = await fetch_from_collection(promoters_collection)

    # Combine into a single list
    all_users.extend(admins)
    all_users.extend(students)
    all_users.extend(schools)
    all_users.extend(promoters)

    return {
        "total_users": len(all_users),
        "users": all_users
    }