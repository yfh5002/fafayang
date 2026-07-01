package com.example.jizhanggongju.model;

public class Account {
    private long id;
    private String name;
    private String icon;
    private String color;
    private double balance;
    private boolean isDefault;
    private long createdAt;

    public Account() {}

    public Account(String name, String icon, String color, double balance) {
        this.name = name;
        this.icon = icon;
        this.color = color;
        this.balance = balance;
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

    public double getBalance() { return balance; }
    public void setBalance(double balance) { this.balance = balance; }

    public boolean isDefault() { return isDefault; }
    public void setDefault(boolean isDefault) { this.isDefault = isDefault; }

    public long getCreatedAt() { return createdAt; }
    public void setCreatedAt(long createdAt) { this.createdAt = createdAt; }
}
