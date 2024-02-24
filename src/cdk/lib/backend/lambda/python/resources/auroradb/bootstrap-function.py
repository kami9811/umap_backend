import json
import pymysql
import os
import boto3


def get_db_credentials(secret_arn):
    # Create Secrets Manager client
    client = boto3.client('secretsmanager')

    # Get the secret value
    response = client.get_secret_value(SecretId=secret_arn)
    if 'SecretString' in response:
        secret = response['SecretString']
        secret_dict = json.loads(secret)
        return secret_dict['username'], secret_dict['password']
    else:
        raise Exception("Secret does not have a SecretString.")

def handler(event, context):
    try:
        # 環境変数からシークレットのARNを取得
        secret_arn = os.environ['SECRET_ARN']
        # データベースの認証情報を取得
        user, password = get_db_credentials(secret_arn)

        # 環境変数から接続情報を取得
        host = os.environ['DB_HOST']
        database = os.environ['DB_NAME']

        # データベースに接続
        conn = pymysql.connect(
            host=host, 
            user=user, 
            passwd=password, 
            db=database, 
            connect_timeout=600,
        )
        with conn.cursor() as cursor:
            # データベースの作成（存在しない場合）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
            
            # データベースを指定
            cursor.execute(f"USE {database};")
            
            # Create QUESTIONS table
            # Create ORGANIZATIONS table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ORGANIZATIONS (
                    id VARCHAR(64) PRIMARY KEY,
                    data_attributes JSON,
                    is_abstract_data JSON
                );
            """)

            # Create USERS table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS USERS (
                    email VARCHAR(64) PRIMARY KEY,
                    organization_id VARCHAR(64),
                    FOREIGN KEY (organization_id) REFERENCES ORGANIZATIONS(id)
                );
            """)
            
            # Create ITEMS table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ITEMS (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    organization_id VARCHAR(64),
                    data_values JSON,
                    is_abstract_data JSON,
                    FOREIGN KEY (organization_id) REFERENCES ORGANIZATIONS(id)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS QUESTIONS (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    question_user VARCHAR(64),
                    question_title VARCHAR(64),
                    question_text VARCHAR(512),
                    FOREIGN KEY (item_id) REFERENCES ITEMS(id)
                );
            """)
            
            # Create ANSWERS table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ANSWERS (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_id INT,
                    answer_user VARCHAR(64),
                    answer_text VARCHAR(512),
                    FOREIGN KEY (question_id) REFERENCES QUESTIONS(id)
                );
            """)
            
            # Create MESSAGES table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS MESSAGES (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_id INT,
                    text VARCHAR(64),
                    FOREIGN KEY (question_id) REFERENCES QUESTIONS(id)
                );
            """)

            # Drop foreign key constraint temporarily
            cursor.execute("""
                ALTER TABLE USERS DROP FOREIGN KEY USERS_ibfk_1;
            """)
            cursor.execute("""
                ALTER TABLE ITEMS DROP FOREIGN KEY ITEMS_ibfk_1;
            """)
            cursor.execute("""
                ALTER TABLE QUESTIONS DROP FOREIGN KEY QUESTIONS_ibfk_1;
            """)
            cursor.execute("""
                ALTER TABLE ANSWERS DROP FOREIGN KEY ANSWERS_ibfk_1;
            """)
            cursor.execute("""
                ALTER TABLE MESSAGES DROP FOREIGN KEY MESSAGES_ibfk_1;
            """)

            cursor.execute(f"""
                ALTER DATABASE {database} CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci
            """)
            cursor.execute(f"""
                ALTER TABLE USERS CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"""
                ALTER TABLE ORGANIZATIONS CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"""
                ALTER TABLE ITEMS CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"""
                ALTER TABLE QUESTIONS CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"""
                ALTER TABLE ANSWERS CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"""
                ALTER TABLE MESSAGES CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # Recreate foreign key constraint
            cursor.execute("""
                ALTER TABLE USERS ADD CONSTRAINT USERS_ibfk_1 FOREIGN KEY (organization_id) REFERENCES ORGANIZATIONS(id);
            """)
            cursor.execute("""
                ALTER TABLE ITEMS ADD CONSTRAINT ITEMS_ibfk_1 FOREIGN KEY (organization_id) REFERENCES ORGANIZATIONS(id);
            """)
            cursor.execute("""
                ALTER TABLE QUESTIONS ADD CONSTRAINT QUESTIONS_ibfk_1 FOREIGN KEY (organization_id) REFERENCES ORGANIZATIONS(id);
            """)
            cursor.execute("""
                ALTER TABLE ANSWERS ADD CONSTRAINT ANSWERS_ibfk_1 FOREIGN KEY (question_id) REFERENCES QUESTIONS(id);
            """)
            cursor.execute("""
                ALTER TABLE MESSAGES ADD CONSTRAINT MESSAGES_ibfk_1 FOREIGN KEY (question_id) REFERENCES QUESTIONS(id);
            """)
            
            conn.commit()
    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps('Error creating database and table')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully created database and table')
    }
