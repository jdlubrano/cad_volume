require_relative 'db_cxn'

class Part
  @@db = DbCxn.new

  def self.all
    query = <<-SQL
    SELECT p.id, a.id as asset_id, a.file, p.width, p.length, p.thickness,
           p.diameter, p.units, p.estimate_length, p.estimate_width,
           p.estimate_thickness, p.estimate_units, p.estimate_diameter
      FROM parts p, assets a
      WHERE p.id = a.owner_id
        AND a.owner_type = 'Part'
        AND (a.file ILIKE '%.stp' OR a.file ILIKE '%.step')
        AND a.deleted = 'f'
        AND (p.length IS NOT NULL OR p.estimate_length IS NOT NULL)
    SQL

    @@db.exec(query) do |result|
      result.each { |part| yield part }
    end
  end
end

