from orator.migrations import Migration


class CreateCommentsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('comments') as table:
            table.increments('id')
            table.timestamps()
            table.text('commentId').unique()
            table.timestamp('utcTime')


    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('comments')
