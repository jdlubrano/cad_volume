require 'pg'

class DbCxn
  def initialize
    @cxn = PG.connect(dbname: 'test_parts')
  end

  def exec(sql)
    @cxn.exec(sql) { |result| yield result }
  end
end

