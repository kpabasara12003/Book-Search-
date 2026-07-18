-- ==========================================
-- University Library Self-Service System
-- PostgreSQL 16+
-- ==========================================

-- SECTION 1: STUDENTS

CREATE TABLE students (
    student_id      SERIAL PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) UNIQUE,
    phone           VARCHAR(20),
    student_number  VARCHAR(50) UNIQUE NOT NULL,
    nfc_uid         VARCHAR(100) UNIQUE NOT NULL, -- From student ID card
    active_borrows  INT NOT NULL DEFAULT 0,
    is_blocked      BOOLEAN NOT NULL DEFAULT FALSE, -- Blocked when fine is pending
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_nfc_uid        ON students(nfc_uid);
CREATE INDEX idx_students_student_number ON students(student_number);


-- SECTION 2: CATALOG (Categories & Authors)

CREATE TABLE book_categories (
    category_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(150) NOT NULL UNIQUE,
    description   TEXT
);

CREATE TABLE authors (
    author_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_name VARCHAR(150) NOT NULL
);

CREATE INDEX idx_authors_name ON authors(author_name);


-- SECTION 3: BOOKS

CREATE TABLE books (
    book_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    subtitle         VARCHAR(255),
    isbn             VARCHAR(20) UNIQUE,
    publisher        VARCHAR(150),
    edition          VARCHAR(50),
    language         VARCHAR(50),
    publication_year INTEGER,
    pages            INTEGER,
    summary          VARCHAR (250),            -- Used for semantic search embedding
    category_id      INTEGER NOT NULL,
    total_copies     INT NOT NULL DEFAULT 0,    -- Maintained by trigger
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_books_category
        FOREIGN KEY (category_id) REFERENCES book_categories(category_id)
);

CREATE INDEX idx_books_title            ON books(title);
CREATE INDEX idx_books_isbn             ON books(isbn);
CREATE INDEX idx_books_category         ON books(category_id);
CREATE INDEX idx_books_publication_year ON books(publication_year);

CREATE TABLE book_authors (
    book_id   INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    PRIMARY KEY (book_id, author_id),

    CONSTRAINT fk_book_authors_book
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    CONSTRAINT fk_book_authors_author
        FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
);


-- SECTION 4: LIBRARY PHYSICAL HIERARCHY
-- Floor → Section → Shelf → Row
-- 

CREATE TABLE library_floors (
    floor_id    SERIAL PRIMARY KEY,
    floor_name  VARCHAR(50) NOT NULL,   -- e.g., 'Ground', '1st', '2nd', '3rd'
    description TEXT
);

CREATE TABLE sections (
    section_id   SERIAL PRIMARY KEY,
    floor_id     INT NOT NULL,
    section_code VARCHAR(10) NOT NULL,  -- e.g., 'A', 'B', 'C'
    section_name VARCHAR(100),          -- e.g., 'Science & Technology'

    FOREIGN KEY (floor_id) REFERENCES library_floors(floor_id),
    UNIQUE (floor_id, section_code)
);

CREATE INDEX idx_sections_floor ON sections(floor_id);

CREATE TABLE bookshelves (
    shelf_id    SERIAL PRIMARY KEY,
    section_id  INT NOT NULL,
    shelf_code  VARCHAR(10) NOT NULL,  -- e.g., '1', '2', '3'

    FOREIGN KEY (section_id) REFERENCES sections(section_id) ON DELETE CASCADE,
    UNIQUE (section_id, shelf_code)
);

CREATE INDEX idx_bookshelves_section ON bookshelves(section_id);

CREATE TABLE shelf_rows (
    row_id       SERIAL PRIMARY KEY,
    shelf_id     INT NOT NULL,
    row_position VARCHAR(20) NOT NULL,  -- e.g., 'Top', 'Middle', 'Bottom'
    category_id  INT NOT NULL,          -- Each row is assigned a category

    FOREIGN KEY (shelf_id) REFERENCES bookshelves(shelf_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES book_categories(category_id),
    UNIQUE (shelf_id, row_position)
);

CREATE INDEX idx_shelf_rows_shelf    ON shelf_rows(shelf_id);
CREATE INDEX idx_shelf_rows_category ON shelf_rows(category_id);


-- SECTION 5: BOOK COPIES (Physical NFC-tagged items)

CREATE TABLE book_copies (
    copy_id    SERIAL PRIMARY KEY,
    book_id    INT NOT NULL,
    row_id     INT NOT NULL,
    nfc_id     VARCHAR(100) UNIQUE NOT NULL,  -- NFC/RFID tag on the physical book
    status     VARCHAR(10) NOT NULL DEFAULT 'available',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (row_id) REFERENCES shelf_rows(row_id),
    CONSTRAINT chk_book_copy_status
        CHECK (status IN ('available', 'borrowed', 'lost', 'damaged'))
);

CREATE INDEX idx_copies_book    ON book_copies(book_id);
CREATE INDEX idx_copies_row     ON book_copies(row_id);
CREATE INDEX idx_copies_nfc_id  ON book_copies(nfc_id);
CREATE INDEX idx_copies_status  ON book_copies(status);


-- SECTION 6: BORROWING & RETURN

CREATE TABLE borrows (
    borrow_id   SERIAL PRIMARY KEY,
    copy_id     INT NOT NULL,
    student_id  INT NOT NULL,
    borrowed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_date    DATE NOT NULL,           -- Default: borrowed_at + 14 days
    returned_at TIMESTAMP WITH TIME ZONE NULL,
    fine_issued BOOLEAN NOT NULL DEFAULT FALSE,

    FOREIGN KEY (copy_id)    REFERENCES book_copies(copy_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE INDEX idx_borrows_student     ON borrows(student_id);
CREATE INDEX idx_borrows_copy        ON borrows(copy_id);
CREATE INDEX idx_borrows_returned_at ON borrows(returned_at);


-- SECTION 7: FINES (Auto-generated on overdue return)
=
CREATE TABLE fines (
    fine_id    SERIAL PRIMARY KEY,
    borrow_id  INT NOT NULL REFERENCES borrows(borrow_id),
    student_id INT NOT NULL REFERENCES students(student_id),
    amount     NUMERIC(8, 2) NOT NULL,
    status     VARCHAR(10) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'paid', 'waived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fines_student ON fines(student_id);
CREATE INDEX idx_fines_borrow  ON fines(borrow_id);
CREATE INDEX idx_fines_status  ON fines(status);


-- SECTION 8: AUTOMATION TRIGGERS

-- Trigger function: auto-update books.total_copies when a copy is added/removed
CREATE OR REPLACE FUNCTION sync_total_copies()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE books SET total_copies = total_copies + 1 WHERE book_id = NEW.book_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE books SET total_copies = total_copies - 1 WHERE book_id = OLD.book_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_total_copies
AFTER INSERT OR DELETE ON book_copies
FOR EACH ROW EXECUTE FUNCTION sync_total_copies();
