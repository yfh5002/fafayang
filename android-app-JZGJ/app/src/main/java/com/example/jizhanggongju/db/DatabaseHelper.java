package com.example.jizhanggongju.db;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import com.example.jizhanggongju.model.Account;
import com.example.jizhanggongju.model.Category;
import com.example.jizhanggongju.model.Record;

import java.util.ArrayList;
import java.util.List;

public class DatabaseHelper extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "jzgj.db";
    private static final int DATABASE_VERSION = 1;

    // 表名
    public static final String TABLE_CATEGORIES = "categories";
    public static final String TABLE_RECORDS = "records";
    public static final String TABLE_ACCOUNTS = "accounts";

    // 通用列
    public static final String COLUMN_ID = "id";

    // Category列
    public static final String COLUMN_NAME = "name";
    public static final String COLUMN_ICON = "icon";
    public static final String COLUMN_COLOR = "color";
    public static final String COLUMN_TYPE = "type";
    public static final String COLUMN_IS_DEFAULT = "is_default";
    public static final String COLUMN_CREATED_AT = "created_at";

    // Record列
    public static final String COLUMN_AMOUNT = "amount";
    public static final String COLUMN_CATEGORY_ID = "category_id";
    public static final String COLUMN_CATEGORY_NAME = "category_name";
    public static final String COLUMN_CATEGORY_COLOR = "category_color";
    public static final String COLUMN_CATEGORY_ICON = "category_icon";
    public static final String COLUMN_ACCOUNT_ID = "account_id";
    public static final String COLUMN_ACCOUNT_NAME = "account_name";
    public static final String COLUMN_NOTE = "note";
    public static final String COLUMN_DATE = "date";

    // Account列
    public static final String COLUMN_BALANCE = "balance";

    private static DatabaseHelper instance;

    public static synchronized DatabaseHelper getInstance(Context context) {
        if (instance == null) {
            instance = new DatabaseHelper(context.getApplicationContext());
        }
        return instance;
    }

    private DatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        // 创建分类表
        String createCategories = "CREATE TABLE " + TABLE_CATEGORIES + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_NAME + " TEXT NOT NULL, " +
                COLUMN_ICON + " TEXT, " +
                COLUMN_COLOR + " TEXT, " +
                COLUMN_TYPE + " INTEGER DEFAULT 0, " +
                COLUMN_IS_DEFAULT + " INTEGER DEFAULT 0, " +
                COLUMN_CREATED_AT + " INTEGER)";
        db.execSQL(createCategories);

        // 创建账户表
        String createAccounts = "CREATE TABLE " + TABLE_ACCOUNTS + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_NAME + " TEXT NOT NULL, " +
                COLUMN_ICON + " TEXT, " +
                COLUMN_COLOR + " TEXT, " +
                COLUMN_BALANCE + " REAL DEFAULT 0, " +
                COLUMN_IS_DEFAULT + " INTEGER DEFAULT 0, " +
                COLUMN_CREATED_AT + " INTEGER)";
        db.execSQL(createAccounts);

        // 创建记录表
        String createRecords = "CREATE TABLE " + TABLE_RECORDS + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_AMOUNT + " REAL NOT NULL, " +
                COLUMN_TYPE + " INTEGER DEFAULT 0, " +
                COLUMN_CATEGORY_ID + " INTEGER, " +
                COLUMN_CATEGORY_NAME + " TEXT, " +
                COLUMN_CATEGORY_COLOR + " TEXT, " +
                COLUMN_CATEGORY_ICON + " TEXT, " +
                COLUMN_ACCOUNT_ID + " INTEGER, " +
                COLUMN_ACCOUNT_NAME + " TEXT, " +
                COLUMN_NOTE + " TEXT, " +
                COLUMN_DATE + " INTEGER, " +
                COLUMN_CREATED_AT + " INTEGER)";
        db.execSQL(createRecords);

        // 插入默认分类
        insertDefaultCategories(db);
        // 插入默认账户
        insertDefaultAccounts(db);
    }

    private void insertDefaultCategories(SQLiteDatabase db) {
        String[][] expenseCategories = {
            {"餐饮", "fa-utensils", "#EF4444"},
            {"交通", "fa-car", "#3B82F6"},
            {"购物", "fa-shopping-bag", "#EC4899"},
            {"娱乐", "fa-film", "#8B5CF6"},
            {"医疗", "fa-heartbeat", "#10B981"},
            {"教育", "fa-graduation-cap", "#F59E0B"},
            {"居住", "fa-home", "#6366F1"},
            {"通讯", "fa-phone", "#14B8A6"}
        };
        String[][] incomeCategories = {
            {"工资", "fa-wallet", "#10B981"},
            {"奖金", "fa-gift", "#F59E0B"},
            {"投资", "fa-chart-line", "#6366F1"},
            {"兼职", "fa-briefcase", "#8B5CF6"},
            {"其他", "fa-coins", "#6B7280"}
        };

        for (String[] cat : expenseCategories) {
            ContentValues values = new ContentValues();
            values.put(COLUMN_NAME, cat[0]);
            values.put(COLUMN_ICON, cat[1]);
            values.put(COLUMN_COLOR, cat[2]);
            values.put(COLUMN_TYPE, 0);
            values.put(COLUMN_IS_DEFAULT, 1);
            values.put(COLUMN_CREATED_AT, System.currentTimeMillis());
            db.insert(TABLE_CATEGORIES, null, values);
        }

        for (String[] cat : incomeCategories) {
            ContentValues values = new ContentValues();
            values.put(COLUMN_NAME, cat[0]);
            values.put(COLUMN_ICON, cat[1]);
            values.put(COLUMN_COLOR, cat[2]);
            values.put(COLUMN_TYPE, 1);
            values.put(COLUMN_IS_DEFAULT, 1);
            values.put(COLUMN_CREATED_AT, System.currentTimeMillis());
            db.insert(TABLE_CATEGORIES, null, values);
        }
    }

    private void insertDefaultAccounts(SQLiteDatabase db) {
        String[][] accounts = {
            {"现金", "fa-money-bill", "#10B981"},
            {"支付宝", "fa-alipay", "#1677FF"},
            {"微信", "fa-weixin", "#07C160"},
            {"银行卡", "fa-credit-card", "#6366F1"}
        };

        for (String[] acc : accounts) {
            ContentValues values = new ContentValues();
            values.put(COLUMN_NAME, acc[0]);
            values.put(COLUMN_ICON, acc[1]);
            values.put(COLUMN_COLOR, acc[2]);
            values.put(COLUMN_BALANCE, 0);
            values.put(COLUMN_IS_DEFAULT, 1);
            values.put(COLUMN_CREATED_AT, System.currentTimeMillis());
            db.insert(TABLE_ACCOUNTS, null, values);
        }
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_RECORDS);
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_CATEGORIES);
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_ACCOUNTS);
        onCreate(db);
    }

    // ==================== Category 操作 ====================
    public long insertCategory(Category category) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_NAME, category.getName());
        values.put(COLUMN_ICON, category.getIcon());
        values.put(COLUMN_COLOR, category.getColor());
        values.put(COLUMN_TYPE, category.getType());
        values.put(COLUMN_IS_DEFAULT, category.isDefault() ? 1 : 0);
        values.put(COLUMN_CREATED_AT, category.getCreatedAt());
        return db.insert(TABLE_CATEGORIES, null, values);
    }

    public List<Category> getCategoriesByType(int type) {
        List<Category> list = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.query(TABLE_CATEGORIES, null, COLUMN_TYPE + "=?",
                new String[]{String.valueOf(type)}, null, null, COLUMN_ID + " ASC");
        if (cursor.moveToFirst()) {
            do {
                Category cat = new Category();
                cat.setId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)));
                cat.setName(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_NAME)));
                cat.setIcon(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ICON)));
                cat.setColor(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_COLOR)));
                cat.setType(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_TYPE)));
                cat.setDefault(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_IS_DEFAULT)) == 1);
                cat.setCreatedAt(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_CREATED_AT)));
                list.add(cat);
            } while (cursor.moveToNext());
        }
        cursor.close();
        return list;
    }

    public Category getCategoryById(long id) {
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.query(TABLE_CATEGORIES, null, COLUMN_ID + "=?",
                new String[]{String.valueOf(id)}, null, null, null);
        Category cat = null;
        if (cursor.moveToFirst()) {
            cat = new Category();
            cat.setId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)));
            cat.setName(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_NAME)));
            cat.setIcon(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ICON)));
            cat.setColor(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_COLOR)));
            cat.setType(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_TYPE)));
            cat.setDefault(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_IS_DEFAULT)) == 1);
            cat.setCreatedAt(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_CREATED_AT)));
        }
        cursor.close();
        return cat;
    }

    public int updateCategory(Category category) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_NAME, category.getName());
        values.put(COLUMN_ICON, category.getIcon());
        values.put(COLUMN_COLOR, category.getColor());
        return db.update(TABLE_CATEGORIES, values, COLUMN_ID + "=?", new String[]{String.valueOf(category.getId())});
    }

    public int deleteCategory(long id) {
        SQLiteDatabase db = this.getWritableDatabase();
        return db.delete(TABLE_CATEGORIES, COLUMN_ID + "=?", new String[]{String.valueOf(id)});
    }

    // ==================== Account 操作 ====================
    public long insertAccount(Account account) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_NAME, account.getName());
        values.put(COLUMN_ICON, account.getIcon());
        values.put(COLUMN_COLOR, account.getColor());
        values.put(COLUMN_BALANCE, account.getBalance());
        values.put(COLUMN_IS_DEFAULT, account.isDefault() ? 1 : 0);
        values.put(COLUMN_CREATED_AT, account.getCreatedAt());
        return db.insert(TABLE_ACCOUNTS, null, values);
    }

    public List<Account> getAllAccounts() {
        List<Account> list = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.query(TABLE_ACCOUNTS, null, null, null, null, null, COLUMN_ID + " ASC");
        if (cursor.moveToFirst()) {
            do {
                Account acc = new Account();
                acc.setId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)));
                acc.setName(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_NAME)));
                acc.setIcon(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ICON)));
                acc.setColor(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_COLOR)));
                acc.setBalance(cursor.getDouble(cursor.getColumnIndexOrThrow(COLUMN_BALANCE)));
                acc.setDefault(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_IS_DEFAULT)) == 1);
                acc.setCreatedAt(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_CREATED_AT)));
                list.add(acc);
            } while (cursor.moveToNext());
        }
        cursor.close();
        return list;
    }

    public Account getAccountById(long id) {
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.query(TABLE_ACCOUNTS, null, COLUMN_ID + "=?",
                new String[]{String.valueOf(id)}, null, null, null);
        Account acc = null;
        if (cursor.moveToFirst()) {
            acc = new Account();
            acc.setId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)));
            acc.setName(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_NAME)));
            acc.setIcon(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ICON)));
            acc.setColor(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_COLOR)));
            acc.setBalance(cursor.getDouble(cursor.getColumnIndexOrThrow(COLUMN_BALANCE)));
            acc.setDefault(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_IS_DEFAULT)) == 1);
            acc.setCreatedAt(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_CREATED_AT)));
        }
        cursor.close();
        return acc;
    }

    public int updateAccount(Account account) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_NAME, account.getName());
        values.put(COLUMN_ICON, account.getIcon());
        values.put(COLUMN_COLOR, account.getColor());
        values.put(COLUMN_BALANCE, account.getBalance());
        return db.update(TABLE_ACCOUNTS, values, COLUMN_ID + "=?", new String[]{String.valueOf(account.getId())});
    }

    public int deleteAccount(long id) {
        SQLiteDatabase db = this.getWritableDatabase();
        return db.delete(TABLE_ACCOUNTS, COLUMN_ID + "=?", new String[]{String.valueOf(id)});
    }

    // ==================== Record 操作 ====================
    public long insertRecord(Record record) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_AMOUNT, record.getAmount());
        values.put(COLUMN_TYPE, record.getType());
        values.put(COLUMN_CATEGORY_ID, record.getCategoryId());
        values.put(COLUMN_CATEGORY_NAME, record.getCategoryName());
        values.put(COLUMN_CATEGORY_COLOR, record.getCategoryColor());
        values.put(COLUMN_CATEGORY_ICON, record.getCategoryIcon());
        values.put(COLUMN_ACCOUNT_ID, record.getAccountId());
        values.put(COLUMN_ACCOUNT_NAME, record.getAccountName());
        values.put(COLUMN_NOTE, record.getNote());
        values.put(COLUMN_DATE, record.getDate());
        values.put(COLUMN_CREATED_AT, record.getCreatedAt());
        return db.insert(TABLE_RECORDS, null, values);
    }

    public List<Record> getRecordsByMonth(int year, int month) {
        List<Record> list = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();
        
        long startTime = getMonthStart(year, month);
        long endTime = getMonthEnd(year, month);
        
        Cursor cursor = db.query(TABLE_RECORDS, null, COLUMN_DATE + ">=? AND " + COLUMN_DATE + "<?",
                new String[]{String.valueOf(startTime), String.valueOf(endTime)}, null, null, COLUMN_DATE + " DESC");
        if (cursor.moveToFirst()) {
            do {
                Record record = cursorToRecord(cursor);
                list.add(record);
            } while (cursor.moveToNext());
        }
        cursor.close();
        return list;
    }

    public List<Record> getAllRecords() {
        List<Record> list = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.query(TABLE_RECORDS, null, null, null, null, null, COLUMN_DATE + " DESC");
        if (cursor.moveToFirst()) {
            do {
                Record record = cursorToRecord(cursor);
                list.add(record);
            } while (cursor.moveToNext());
        }
        cursor.close();
        return list;
    }

    public double getTotalByTypeAndMonth(int type, int year, int month) {
        SQLiteDatabase db = this.getReadableDatabase();
        long startTime = getMonthStart(year, month);
        long endTime = getMonthEnd(year, month);
        
        String query = "SELECT SUM(" + COLUMN_AMOUNT + ") FROM " + TABLE_RECORDS + 
                " WHERE " + COLUMN_TYPE + "=? AND " + COLUMN_DATE + ">=? AND " + COLUMN_DATE + "<?";
        Cursor cursor = db.rawQuery(query, new String[]{String.valueOf(type), String.valueOf(startTime), String.valueOf(endTime)});
        double total = 0;
        if (cursor.moveToFirst()) {
            total = cursor.getDouble(0);
        }
        cursor.close();
        return total;
    }

    private Record cursorToRecord(Cursor cursor) {
        Record record = new Record();
        record.setId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)));
        record.setAmount(cursor.getDouble(cursor.getColumnIndexOrThrow(COLUMN_AMOUNT)));
        record.setType(cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_TYPE)));
        record.setCategoryId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_CATEGORY_ID)));
        record.setCategoryName(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_CATEGORY_NAME)));
        record.setCategoryColor(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_CATEGORY_COLOR)));
        record.setCategoryIcon(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_CATEGORY_ICON)));
        record.setAccountId(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ACCOUNT_ID)));
        record.setAccountName(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ACCOUNT_NAME)));
        record.setNote(cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_NOTE)));
        record.setDate(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_DATE)));
        record.setCreatedAt(cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_CREATED_AT)));
        return record;
    }

    private long getMonthStart(int year, int month) {
        java.util.Calendar cal = java.util.Calendar.getInstance();
        cal.set(year, month - 1, 1, 0, 0, 0);
        cal.set(java.util.Calendar.MILLISECOND, 0);
        return cal.getTimeInMillis();
    }

    private long getMonthEnd(int year, int month) {
        java.util.Calendar cal = java.util.Calendar.getInstance();
        cal.set(year, month - 1, 1, 23, 59, 59);
        cal.set(java.util.Calendar.MILLISECOND, 999);
        cal.set(java.util.Calendar.DAY_OF_MONTH, cal.getActualMaximum(java.util.Calendar.DAY_OF_MONTH));
        return cal.getTimeInMillis();
    }

    public int deleteRecord(long id) {
        SQLiteDatabase db = this.getWritableDatabase();
        return db.delete(TABLE_RECORDS, COLUMN_ID + "=?", new String[]{String.valueOf(id)});
    }
}
