import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
from pathlib import Path

# ============================================================
# CẤU HÌNH
# ============================================================

st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "hotel_management.db"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống',
            guest_name TEXT DEFAULT '',
            guest_phone TEXT DEFAULT '',
            guest_id TEXT DEFAULT '',
            check_in TEXT DEFAULT '',
            check_out TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            phone TEXT,
            identity TEXT,
            room_number TEXT NOT NULL,
            room_type TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            guests INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Đã đặt',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            guest_name TEXT,
            transaction_type TEXT NOT NULL,
            amount REAL DEFAULT 0,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Tạo dữ liệu phòng mẫu nếu database chưa có phòng
    cursor.execute("SELECT COUNT(*) FROM rooms")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_rooms = [
            ("101", "Standard", 800000),
            ("102", "Standard", 800000),
            ("103", "Standard", 800000),
            ("104", "Standard", 800000),
            ("201", "Deluxe", 1200000),
            ("202", "Deluxe", 1200000),
            ("203", "Deluxe", 1200000),
            ("204", "Deluxe", 1200000),
            ("301", "Suite", 2500000),
            ("302", "Suite", 2500000),
            ("303", "Suite", 2500000),
            ("304", "Suite", 2500000),
        ]

        cursor.executemany("""
            INSERT INTO rooms
            (room_number, room_type, price)
            VALUES (?, ?, ?)
        """, sample_rooms)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# HÀM DATABASE
# ============================================================

def query_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def format_money(value):
    return f"{value:,.0f} VNĐ"


def get_room(room_number):
    df = query_df(
        "SELECT * FROM rooms WHERE room_number = ?",
        (room_number,)
    )

    if df.empty:
        return None

    return df.iloc[0]


def get_all_rooms():
    return query_df(
        "SELECT * FROM rooms ORDER BY room_number"
    )


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

.hotel-title {
    font-size: 32px;
    font-weight: 700;
}

.room-card {
    padding: 15px;
    border-radius: 12px;
    background: white;
    border: 1px solid #ddd;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🏨 HOTEL SYSTEM")
st.sidebar.caption("Hotel Room Management")

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Dashboard",
        "🛏️ Quản lý phòng",
        "📝 Đặt phòng",
        "🔑 Check-in",
        "🚪 Check-out",
        "🧹 Housekeeping",
        "🔎 Tìm kiếm",
        "📋 Lịch sử giao dịch",
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    f"Database: {DB_FILE}"
)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "📊 Dashboard":

    st.title("📊 Dashboard")

    rooms = get_all_rooms()

    total_rooms = len(rooms)

    empty_rooms = len(
        rooms[rooms["status"] == "Trống"]
    )

    occupied_rooms = len(
        rooms[rooms["status"] == "Đang ở"]
    )

    reserved_rooms = len(
        rooms[rooms["status"] == "Đã đặt"]
    )

    cleaning_rooms = len(
        rooms[rooms["status"] == "Đang dọn"]
    )

    maintenance_rooms = len(
        rooms[rooms["status"] == "Bảo trì"]
    )

    occupancy_rate = (
        occupied_rooms / total_rooms * 100
        if total_rooms > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🏨 Tổng phòng",
        total_rooms
    )

    col2.metric(
        "🟢 Phòng trống",
        empty_rooms
    )

    col3.metric(
        "🔴 Đang ở",
        occupied_rooms
    )

    col4.metric(
        "🟡 Đã đặt",
        reserved_rooms
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "🧹 Đang dọn",
        cleaning_rooms
    )

    col2.metric(
        "🔧 Bảo trì",
        maintenance_rooms
    )

    col3.metric(
        "📈 Công suất",
        f"{occupancy_rate:.1f}%"
    )

    st.divider()

    st.subheader("🛏️ Tình trạng phòng")

    display = rooms[
        [
            "room_number",
            "room_type",
            "price",
            "status",
            "guest_name"
        ]
    ].copy()

    display.columns = [
        "Số phòng",
        "Loại phòng",
        "Giá/đêm",
        "Trạng thái",
        "Khách"
    ]

    display["Giá/đêm"] = display[
        "Giá/đêm"
    ].apply(format_money)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# QUẢN LÝ PHÒNG
# ============================================================

elif menu == "🛏️ Quản lý phòng":

    st.title("🛏️ Quản lý phòng")

    rooms = get_all_rooms()

    col1, col2 = st.columns(2)

    with col1:

        status = st.selectbox(
            "Lọc trạng thái",
            [
                "Tất cả",
                "Trống",
                "Đang ở",
                "Đã đặt",
                "Đang dọn",
                "Bảo trì"
            ]
        )

    with col2:

        room_type = st.selectbox(
            "Lọc loại phòng",
            ["Tất cả"] +
            sorted(rooms["room_type"].unique())
        )

    filtered = rooms.copy()

    if status != "Tất cả":
        filtered = filtered[
            filtered["status"] == status
        ]

    if room_type != "Tất cả":
        filtered = filtered[
            filtered["room_type"] == room_type
        ]

    display = filtered[
        [
            "room_number",
            "room_type",
            "price",
            "status",
            "guest_name"
        ]
    ].copy()

    display.columns = [
        "Số phòng",
        "Loại phòng",
        "Giá/đêm",
        "Trạng thái",
        "Khách"
    ]

    display["Giá/đêm"] = display[
        "Giá/đêm"
    ].apply(format_money)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("⚙️ Cập nhật trạng thái phòng")

    room_number = st.selectbox(
        "Chọn phòng",
        rooms["room_number"].tolist()
    )

    current_room = get_room(room_number)

    st.info(
        f"Phòng {room_number} hiện tại: "
        f"{current_room['status']}"
    )

    new_status = st.selectbox(
        "Trạng thái mới",
        [
            "Trống",
            "Đang ở",
            "Đã đặt",
            "Đang dọn",
            "Bảo trì"
        ]
    )

    if st.button(
        "💾 Cập nhật",
        use_container_width=True
    ):

        execute_query(
            """
            UPDATE rooms
            SET status = ?
            WHERE room_number = ?
            """,
            (new_status, room_number)
        )

        st.success(
            f"Phòng {room_number} → {new_status}"
        )

        st.rerun()


# ============================================================
# ĐẶT PHÒNG
# ============================================================

elif menu == "📝 Đặt phòng":

    st.title("📝 Đặt phòng")

    rooms = get_all_rooms()

    available = rooms[
        rooms["status"] == "Trống"
    ]

    if available.empty:

        st.warning(
            "Hiện không có phòng trống."
        )

    else:

        with st.form("reservation_form"):

            st.subheader(
                "Thông tin khách"
            )

            col1, col2 = st.columns(2)

            with col1:

                guest_name = st.text_input(
                    "Họ và tên *"
                )

                phone = st.text_input(
                    "Số điện thoại"
                )

                identity = st.text_input(
                    "CCCD / Passport"
                )

            with col2:

                room_number = st.selectbox(
                    "Phòng *",
                    available["room_number"].tolist()
                )

                guests = st.number_input(
                    "Số khách",
                    min_value=1,
                    max_value=20,
                    value=1
                )

            col1, col2 = st.columns(2)

            with col1:

                check_in = st.date_input(
                    "Ngày nhận phòng",
                    date.today()
                )

            with col2:

                check_out = st.date_input(
                    "Ngày trả phòng",
                    date.today()
                )

            submit = st.form_submit_button(
                "📌 Xác nhận đặt phòng",
                use_container_width=True
            )

            if submit:

                if not guest_name.strip():

                    st.error(
                        "Vui lòng nhập tên khách."
                    )

                elif check_out <= check_in:

                    st.error(
                        "Ngày trả phòng phải sau ngày nhận phòng."
                    )

                else:

                    room = get_room(room_number)

                    execute_query(
                        """
                        INSERT INTO reservations
                        (
                            guest_name,
                            phone,
                            identity,
                            room_number,
                            room_type,
                            check_in,
                            check_out,
                            guests,
                            status,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            guest_name,
                            phone,
                            identity,
                            room_number,
                            room["room_type"],
                            str(check_in),
                            str(check_out),
                            guests,
                            "Đã đặt",
                            datetime.now().isoformat()
                        )
                    )

                    execute_query(
                        """
                        UPDATE rooms
                        SET
                            status = 'Đã đặt',
                            guest_name = ?,
                            guest_phone = ?,
                            guest_id = ?,
                            check_in = ?,
                            check_out = ?
                        WHERE room_number = ?
                        """,
                        (
                            guest_name,
                            phone,
                            identity,
                            str(check_in),
                            str(check_out),
                            room_number
                        )
                    )

                    st.success(
                        f"Đã đặt phòng {room_number} "
                        f"cho {guest_name}."
                    )


# ============================================================
# CHECK-IN
# ============================================================

elif menu == "🔑 Check-in":

    st.title("🔑 Check-in")

    rooms = get_all_rooms()

    checkin_rooms = rooms[
        rooms["status"].isin(
            ["Trống", "Đã đặt"]
        )
    ]

    if checkin_rooms.empty:

        st.warning(
            "Không có phòng có thể check-in."
        )

    else:

        room_number = st.selectbox(
            "Chọn phòng",
            checkin_rooms["room_number"].tolist()
        )

        room = get_room(room_number)

        st.info(
            f"Phòng {room_number} | "
            f"{room['room_type']} | "
            f"{format_money(room['price'])}/đêm"
        )

        col1, col2 = st.columns(2)

        with col1:

            guest_name = st.text_input(
                "Tên khách",
                value=room["guest_name"]
            )

            identity = st.text_input(
                "CCCD / Passport",
                value=room["guest_id"]
            )

        with col2:

            phone = st.text_input(
                "Số điện thoại",
                value=room["guest_phone"]
            )

            guests = st.number_input(
                "Số lượng khách",
                min_value=1,
                value=1
            )

        check_in = st.date_input(
            "Ngày check-in",
            date.today()
        )

        check_out = st.date_input(
            "Ngày dự kiến check-out",
            date.today()
        )

        if st.button(
            "🔑 Xác nhận Check-in",
            use_container_width=True
        ):

            if not guest_name.strip():

                st.error(
                    "Vui lòng nhập tên khách."
                )

            elif check_out <= check_in:

                st.error(
                    "Ngày check-out phải sau ngày check-in."
                )

            else:

                execute_query(
                    """
                    UPDATE rooms
                    SET
                        status = 'Đang ở',
                        guest_name = ?,
                        guest_phone = ?,
                        guest_id = ?,
                        check_in = ?,
                        check_out = ?
                    WHERE room_number = ?
                    """,
                    (
                        guest_name,
                        phone,
                        identity,
                        str(check_in),
                        str(check_out),
                        room_number
                    )
                )

                execute_query(
                    """
                    INSERT INTO transactions
                    (
                        room_number,
                        guest_name,
                        transaction_type,
                        amount,
                        note,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        room_number,
                        guest_name,
                        "CHECK-IN",
                        0,
                        f"{guests} khách",
                        datetime.now().isoformat()
                    )
                )

                st.success(
                    f"Check-in thành công phòng {room_number}."
                )

                st.rerun()


# ============================================================
# CHECK-OUT
# ============================================================

elif menu == "🚪 Check-out":

    st.title("🚪 Check-out")

    rooms = get_all_rooms()

    occupied = rooms[
        rooms["status"] == "Đang ở"
    ]

    if occupied.empty:

        st.info(
            "Hiện không có khách đang lưu trú."
        )

    else:

        room_number = st.selectbox(
            "Phòng check-out",
            occupied["room_number"].tolist()
        )

        room = get_room(room_number)

        st.subheader(
            f"Phòng {room_number}"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Khách",
            room["guest_name"]
        )

        col2.metric(
            "Loại phòng",
            room["room_type"]
        )

        col3.metric(
            "Giá/đêm",
            format_money(room["price"])
        )

        st.divider()

        nights = st.number_input(
            "Số đêm",
            min_value=1,
            value=1
        )

        room_charge = (
            room["price"] * nights
        )

        extra_charge = st.number_input(
            "Chi phí phát sinh",
            min_value=0.0,
            value=0.0,
            step=50000.0
        )

        discount = st.number_input(
            "Giảm giá",
            min_value=0.0,
            value=0.0,
            step=50000.0
        )

        total = (
            room_charge
            + extra_charge
            - discount
        )

        if total < 0:
            total = 0

        st.subheader(
            f"💰 Tổng thanh toán: {format_money(total)}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"Tiền phòng: "
                f"**{format_money(room_charge)}**"
            )

            st.write(
                f"Phát sinh: "
                f"**{format_money(extra_charge)}**"
            )

        with col2:

            st.write(
                f"Giảm giá: "
                f"**{format_money(discount)}**"
            )

        if st.button(
            "🚪 Xác nhận Check-out",
            use_container_width=True
        ):

            execute_query(
                """
                INSERT INTO transactions
                (
                    room_number,
                    guest_name,
                    transaction_type,
                    amount,
                    note,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    room_number,
                    room["guest_name"],
                    "CHECK-OUT",
                    total,
                    "Hoàn tất thanh toán",
                    datetime.now().isoformat()
                )
            )

            execute_query(
                """
                UPDATE rooms
                SET
                    status = 'Đang dọn',
                    guest_name = '',
                    guest_phone = '',
                    guest_id = '',
                    check_in = '',
                    check_out = ''
                WHERE room_number = ?
                """,
                (room_number,)
            )

            st.success(
                f"Check-out thành công phòng {room_number}."
            )

            st.info(
                "Phòng đã chuyển sang trạng thái 'Đang dọn'."
            )

            st.rerun()


# ============================================================
# HOUSEKEEPING
# ============================================================

elif menu == "🧹 Housekeeping":

    st.title("🧹 Housekeeping")

    rooms = get_all_rooms()

    cleaning = rooms[
        rooms["status"] == "Đang dọn"
    ]

    if cleaning.empty:

        st.success(
            "Không có phòng đang chờ dọn."
        )

    else:

        st.subheader(
            f"Phòng cần dọn: {len(cleaning)}"
        )

        st.dataframe(
            cleaning[
                [
                    "room_number",
                    "room_type",
                    "status"
                ]
            ].rename(
                columns={
                    "room_number": "Số phòng",
                    "room_type": "Loại phòng",
                    "status": "Trạng thái"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        room_number = st.selectbox(
            "Chọn phòng đã dọn xong",
            cleaning["room_number"].tolist()
        )

        if st.button(
            "✅ Hoàn tất vệ sinh",
            use_container_width=True
        ):

            execute_query(
                """
                UPDATE rooms
                SET status = 'Trống'
                WHERE room_number = ?
                """,
                (room_number,)
            )

            execute_query(
                """
                INSERT INTO transactions
                (
                    room_number,
                    transaction_type,
                    amount,
                    note,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    room_number,
                    "HOUSEKEEPING",
                    0,
                    "Phòng đã vệ sinh xong",
                    datetime.now().isoformat()
                )
            )

            st.success(
                f"Phòng {room_number} đã sẵn sàng bán."
            )

            st.rerun()


# ============================================================
# TÌM KIẾM
# ============================================================

elif menu == "🔎 Tìm kiếm":

    st.title("🔎 Tìm kiếm")

    keyword = st.text_input(
        "Tìm theo số phòng, tên khách hoặc số điện thoại"
    )

    rooms = get_all_rooms()

    if keyword:

        keyword = keyword.strip()

        result = rooms[
            rooms["room_number"].str.contains(
                keyword,
                case=False,
                na=False
            )
            |
            rooms["guest_name"].str.contains(
                keyword,
                case=False,
                na=False
            )
            |
            rooms["guest_phone"].str.contains(
                keyword,
                case=False,
                na=False
            )
        ]

        if result.empty:

            st.warning(
                "Không tìm thấy dữ liệu."
            )

        else:

            display = result[
                [
                    "room_number",
                    "room_type",
                    "status",
                    "guest_name",
                    "guest_phone",
                    "check_in",
                    "check_out"
                ]
            ].copy()

            display.columns = [
                "Số phòng",
                "Loại phòng",
                "Trạng thái",
                "Khách",
                "SĐT",
                "Check-in",
                "Check-out"
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

    else:

        st.info(
            "Nhập thông tin để tìm kiếm."
        )


# ============================================================
# LỊCH SỬ GIAO DỊCH
# ============================================================

elif menu == "📋 Lịch sử giao dịch":

    st.title("📋 Lịch sử giao dịch")

    transactions = query_df("""
        SELECT
            id,
            room_number,
            guest_name,
            transaction_type,
            amount,
            note,
            created_at
        FROM transactions
        ORDER BY id DESC
    """)

    if transactions.empty:

        st.info(
            "Chưa có giao dịch."
        )

    else:

        display = transactions.copy()

        display.columns = [
            "ID",
            "Phòng",
            "Khách",
            "Loại giao dịch",
            "Số tiền",
            "Ghi chú",
            "Thời gian"
        ]

        display["Số tiền"] = display[
            "Số tiền"
        ].apply(format_money)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        total_revenue = transactions[
            transactions["transaction_type"]
            == "CHECK-OUT"
        ]["amount"].sum()

        st.metric(
            "💰 Doanh thu từ Check-out",
            format_money(total_revenue)
        )
