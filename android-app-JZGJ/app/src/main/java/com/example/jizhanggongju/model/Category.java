package com.example.jizhanggongju.model;

public class Category {
    private long id;
    private String name;
    private String icon;
    private String color;
    private int type; // 0=支出, 1=收入
    private boolean isDefault;
    private long createdAt;

    public Category() {}

    public Category(String name, String icon, String color, int type) {
        this.name = name;
        this.icon = icon;
        this.color = color;
        this.type = type;
        this.isDefault = false;
        this.createdAt = System.currentTimeMillis();
    }

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getIcon() { return icon; }
    public void setIcon(String icon) { this.icon = icon; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public int getType() { return type; }
    public void setType(int type) { this.type = type; }

    public boolean isDefault() { return isDefault; }
    public void setDefault(boolean isDefault) { this.isDefault = isDefault; }

    public long getCreatedAt() { return createdAt; }
    public void setCreatedAt(long createdAt) { this.createdAt = createdAt; }
}
