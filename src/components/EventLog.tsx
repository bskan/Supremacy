import React, { useState, useEffect } from 'react';

interface GameEvent {
  event_id: number;
  turn_number: number;
  planet_name: string;
  event_type: string;
  severity: 'good' | 'bad' | 'neutral';
  description: string;
}

const EventLog: React.FC = () => {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'good' | 'bad'>('all');

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const res = await fetch('/api/events?limit=50');
      if (res.ok) {
        const data: GameEvent[] = await res.json();
        setEvents(data);
      }
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredEvents = events.filter(e => filter === 'all' || e.severity === filter);

  const severityColor = (severity: string) => {
    switch (severity) {
      case 'good': return '#4ade80';
      case 'bad': return '#f87171';
      default: return '#94a3b8';
    }
  };

  const severityIcon = (severity: string) => {
    switch (severity) {
      case 'good': return '✨';
      case 'bad': return '❌';
      default: return '⚪';
    }
  };

  return (
    <div className="event-log" style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>{String.fromCodePoint(0x1f4dd)} Recent Events</h3>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['all', 'good', 'bad'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '4px 12px',
                fontSize: 12,
                border: '1px solid #374151',
                borderRadius: 4,
                background: filter === f ? '#3b82f6' : 'transparent',
                color: filter === f ? '#fff' : '#9ca3af',
                cursor: 'pointer',
              }}
            >
              {f === 'all' ? '⚪ All' : f === 'good' ? '✨ Good' : '❌ Bad'}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div style={{ color: '#9ca3af', fontSize: 13 }}>Loading events...</div>
      ) : filteredEvents.length === 0 ? (
        <div style={{ color: '#9ca3af', fontSize: 13, padding: 16, textAlign: 'center' }}>
          No events yet. Advance a turn to trigger random events!
        </div>
      ) : (
        <div style={{ maxHeight: 300, overflow: 'auto' }}>
          {filteredEvents.map(event => (
            <div
              key={event.event_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 10px',
                borderBottom: '1px solid #1f2937',
                fontSize: 13,
              }}
            >
              <span style={{ color: severityColor(event.severity), fontSize: 14 }}>
                {severityIcon(event.severity)}
              </span>
              <span style={{ color: '#60a5fa', fontWeight: 600, minWidth: 50 }}>
                T{event.turn_number}
              </span>
              <span style={{ color: '#94a3b8', minWidth: 100 }}>
                {event.planet_name}
              </span>
              <span style={{ color: '#e5e7eb' }}>{event.description}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EventLog;
