from orator.migrations import Migration


class CreateConfigurationsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('configurations') as table:
            table.increments('id')
            table.timestamps()
            table.text('version')
            table.text('username')
            table.text('password')
            table.text('clientId')
            table.text('clientSecret')
            table.text('catechismFilename')
            table.text('baltimoreFilename')
            table.text('canonFilename')
            table.text('girmFilename')


    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('configurations')
