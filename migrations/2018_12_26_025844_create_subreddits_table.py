from orator.migrations import Migration


class CreateSubredditsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('subreddits') as table:
            table.increments('id')
            table.timestamps()
            table.text('subreddit').unique()
            table.boolean('isEnabled')
            table.boolean('isSandbox')

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('subreddits')
