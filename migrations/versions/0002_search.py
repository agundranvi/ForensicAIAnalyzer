from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute(
            "CREATE VIRTUAL TABLE artifact_search USING fts5(text, sender, recipient, content='artifacts', content_rowid='id')"
        )
        op.execute(
            "CREATE TRIGGER artifact_search_insert AFTER INSERT ON artifacts BEGIN INSERT INTO artifact_search(rowid,text,sender,recipient) VALUES(new.id,new.text,new.sender,new.recipient); END"
        )
        op.execute(
            "CREATE TRIGGER artifact_search_delete AFTER DELETE ON artifacts BEGIN INSERT INTO artifact_search(artifact_search,rowid,text,sender,recipient) VALUES('delete',old.id,old.text,old.sender,old.recipient); END"
        )
        op.execute("INSERT INTO artifact_search(artifact_search) VALUES('rebuild')")


def downgrade():
    raise RuntimeError("Destructive downgrade disabled")
