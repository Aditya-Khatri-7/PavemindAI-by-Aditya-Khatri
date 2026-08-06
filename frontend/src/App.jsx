import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  Video, 
  Image as ImageIcon, 
  Camera, 
  History, 
  TrendingUp, 
  Download, 
  Trash2, 
  MapPin, 
  RefreshCw, 
  AlertTriangle,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Database,
  BarChart3,
  PieChart as PieIcon,
  Ruler,
  Activity,
  Layers,
  FileSpreadsheet,
  Maximize2,
  Minimize2,
  Maximize,
  Minimize,
  Sun,
  Moon,
  Brain
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  PieChart, 
  Pie, 
  Cell, 
  Legend,
  BarChart,
  Bar,
  CartesianGrid
} from 'recharts';
import L from 'leaflet';

const API_BASE = "http://localhost:8000";

// --- CUSTOM HIGH-TECH LEAFLET MAP ---
const PotholeMap = ({ coordinates, theme, latInput, lonInput, setLatInput, setLonInput }) => {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const tileLayerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;
    
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, {
        center: [latInput || 28.6139, lonInput || 77.2090], // center on selected location or default Delhi
        zoom: 5,
        zoomControl: true
      });
    }

    const map = mapInstance.current;

    // Add or update tile layer based on theme
    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }
    
    tileLayerRef.current = L.tileLayer(
      theme === 'ivory'
        ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 20
      }
    ).addTo(map);

    // Clear previous CircleMarkers (both potholes and selected marker)
    map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    // Add selected location marker if exists
    if (latInput && lonInput) {
      const selectedMarker = L.circleMarker([latInput, lonInput], {
        radius: 8,
        fillColor: 'var(--color-cyan)',
        color: theme === 'ivory' ? '#1e293b' : '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85
      }).addTo(map);

      selectedMarker.bindPopup(`
        <div style="color: var(--text-primary, #f1f5f9); background: var(--panel-bg, #0d1321); font-family: sans-serif; font-size: 11px; padding: 6px; border-radius: 8px; border: 1px solid var(--border-color, rgba(255,255,255,0.06));">
          <b style="color: var(--color-cyan); text-transform: uppercase; font-size: 11px; display: block; margin-bottom: 4px;">Selected Scan Locale</b>
          <div style="height: 1px; background: var(--border-color); margin: 4px 0;"></div>
          Latitude: <b>${latInput.toFixed(5)}</b><br/>
          Longitude: <b>${lonInput.toFixed(5)}</b>
        </div>
      `);
    }

    // Add new pothole markers
    if (coordinates && coordinates.length > 0) {
      coordinates.forEach((coord) => {
        if (!coord.lat || !coord.lon) return;

        const color = coord.severity === 'SEVERE' ? 'var(--color-severe)' : (coord.severity === 'MODERATE' ? 'var(--color-moderate)' : 'var(--color-minor)');
        const marker = L.circleMarker([coord.lat, coord.lon], {
          radius: 6,
          fillColor: color,
          color: theme === 'ivory' ? '#2c3e50' : '#ffffff',
          weight: 1,
          opacity: 0.9,
          fillOpacity: 0.8
        }).addTo(map);

        marker.bindPopup(`
          <div style="color: var(--text-primary, #f1f5f9); background: var(--panel-bg, #0d1321); font-family: sans-serif; font-size: 11px; padding: 6px; border-radius: 8px; border: 1px solid var(--border-color, rgba(255,255,255,0.06));">
            <b style="color: ${color}; text-transform: uppercase; font-size: 12px; display: block; margin-bottom: 4px;">${coord.severity} Severity Pothole</b>
            <div style="height: 1px; background: var(--border-color); margin: 4px 0;"></div>
            Estimated Width: <b>${coord.width_cm ? coord.width_cm.toFixed(1) + ' cm' : 'N/A'}</b><br/>
            Confidence Score: <b>${coord.confidence ? (coord.confidence * 100).toFixed(0) + '%' : 'N/A'}</b><br/>
            GPS Coordinates: <b>${coord.lat.toFixed(5)}, ${coord.lon.toFixed(5)}</b>
          </div>
        `);
      });
    }

    // Add click handler on the map to update default lat/lon
    const onMapClick = (e) => {
      const { lat, lng } = e.latlng;
      setLatInput(parseFloat(lat.toFixed(6)));
      setLonInput(parseFloat(lng.toFixed(6)));
    };

    map.on('click', onMapClick);

    return () => {
      map.off('click', onMapClick);
    };
  }, [coordinates, theme, latInput, lonInput, setLatInput, setLonInput]);

  // Pan map when latInput or lonInput changes externally
  useEffect(() => {
    if (mapInstance.current && latInput && lonInput) {
      mapInstance.current.panTo([latInput, lonInput]);
    }
  }, [latInput, lonInput]);

  return (
    <div className="glass-panel" style={{ overflow: 'hidden', padding: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justify: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MapPin style={{ color: 'var(--color-cyan)' }} size={16} />
          <h3 style={{ fontSize: '14px', fontWeight: '600' }}>GPS POTHOLE HEATMAP</h3>
        </div>
        <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'JetBrains Mono' }}>DATABASE MAPPED: {coordinates?.length || 0} POINTS</span>
      </div>
      {(!coordinates || coordinates.length === 0) ? (
        <div className="fallback-placeholder" style={{ height: '340px' }}>No Data Available</div>
      ) : (
        <div ref={mapRef} style={{ width: '100%', height: '340px', borderRadius: '12px' }} />
      )}
    </div>
  );
};

// --- MAIN APPLICATION INTERFACE ---
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dbConnected, setDbConnected] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('pothole-theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pothole-theme', theme);
  }, [theme]);
  
  // Real Statistics state
  const [stats, setStats] = useState({
    total_scans: 0,
    total_potholes: 0,
    minor: 0,
    moderate: 0,
    severe: 0,
    avg_health_score: 100,
    coordinates: [],
    trends: []
  });
  const [loadingStats, setLoadingStats] = useState(true);

  // History & Uploads
  const [scans, setScans] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeScanDetail, setActiveScanDetail] = useState(null);

  // Image Upload State
  const [imageResults, setImageResults] = useState([]);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [selectedResultIdx, setSelectedResultIdx] = useState(0);

  // Video Upload State
  const [videoFile, setVideoFile] = useState(null);
  const [videoProgress, setVideoProgress] = useState(null);
  const [videoStatus, setVideoStatus] = useState(null);
  const [videoScanId, setVideoScanId] = useState(null);
  const [videoResult, setVideoResult] = useState(null);
  const [latInput, setLatInput] = useState(28.6139);
  const [lonInput, setLonInput] = useState(77.2090);

  // Webcam State
  const [webcamActive, setWebcamActive] = useState(false);
  const [livePotholes, setLivePotholes] = useState([]);
  const [liveCondition, setLiveCondition] = useState({ label: 'GOOD', color: 'var(--color-minor)', alert: 'Road Profile Clear' });
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const webcamInterval = useRef(null);
  const currentGPS = useRef({ lat: 28.6139, lon: 77.2090 });

  // --- REDESIGN CUSTOM STATES & REFS ---
  const [videoPanelWidth, setVideoPanelWidth] = useState(() => {
    const saved = localStorage.getItem('pothole-video-panel-width');
    return saved ? parseFloat(saved) : 55;
  });
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef(null);

  const [imagePanelWidth, setImagePanelWidth] = useState(() => {
    const saved = localStorage.getItem('pothole-image-panel-width');
    return saved ? parseFloat(saved) : 25;
  });
  const [isImageResizing, setIsImageResizing] = useState(false);
  const imageContainerRef = useRef(null);

  const [videoTime, setVideoTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const processedVideoRef = useRef(null);
  
  const [videoCacheBuster, setVideoCacheBuster] = useState(Date.now());
  useEffect(() => {
    setVideoCacheBuster(Date.now());
  }, [videoResult]);

  const [maximizedCard, setMaximizedCard] = useState(null);
  const [videoDetailTab, setVideoDetailTab] = useState('events');

  const logsContainerRef = useRef(null);
  const [eventSearch, setEventSearch] = useState('');
  const [eventSeverityFilter, setEventSeverityFilter] = useState({
    MINOR: true,
    MODERATE: true,
    SEVERE: true
  });

  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsResizing(true);
  };

  const handleImageMouseDown = (e) => {
    e.preventDefault();
    setIsImageResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing || !containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      if (newLeftWidth > 20 && newLeftWidth < 80) {
        setVideoPanelWidth(newLeftWidth);
        localStorage.setItem('pothole-video-panel-width', newLeftWidth.toString());
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.classList.add('is-resizing');
    } else {
      document.body.classList.remove('is-resizing');
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.classList.remove('is-resizing');
    };
  }, [isResizing]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isImageResizing || !imageContainerRef.current) return;
      const containerRect = imageContainerRef.current.getBoundingClientRect();
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      if (newLeftWidth > 15 && newLeftWidth < 60) {
        setImagePanelWidth(newLeftWidth);
        localStorage.setItem('pothole-image-panel-width', newLeftWidth.toString());
      }
    };

    const handleMouseUp = () => {
      setIsImageResizing(false);
    };

    if (isImageResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.classList.add('is-resizing');
    } else {
      document.body.classList.remove('is-resizing');
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.classList.remove('is-resizing');
    };
  }, [isImageResizing]);

  const renderMaximizeButton = (cardId) => {
    const isMax = maximizedCard === cardId;
    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          setMaximizedCard(isMax ? null : cardId);
        }}
        className="maximize-btn"
        title={isMax ? "Restore Down" : "Maximize Card"}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#64748b',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          padding: '4px',
          borderRadius: '4px',
          transition: 'color 0.2s',
        }}
      >
        {isMax ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
      </button>
    );
  };

  const fetchAnalytics = async () => {
    setLoadingStats(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setDbConnected(data.db_connected);
      }
    } catch (e) {
      console.error("Failed to load statistics:", e);
    } finally {
      setLoadingStats(false);
    }
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/api/scans`);
      if (res.ok) {
        const data = await res.json();
        setScans(data);
      }
    } catch (e) {
      console.error("Failed to load scans:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    fetchHistory();
  }, []);

  // Monitor video processing progress in background
  useEffect(() => {
    let interval;
    if (videoScanId && videoStatus === 'processing') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/api/scans/${videoScanId}`);
          if (res.ok) {
            const data = await res.json();
            setVideoProgress(data.scan.progress);
            if (data.scan.status === 'completed') {
              setVideoStatus('completed');
              setVideoResult(data);
              setVideoScanId(null);
              fetchAnalytics();
              fetchHistory();
            } else if (data.scan.status === 'failed') {
              setVideoStatus('failed');
              setVideoScanId(null);
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [videoScanId, videoStatus]);

  // Handle Multi Image Upload
  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    
    setUploadingImages(true);
    const formData = new FormData();
    files.forEach(file => {
      formData.append("files", file);
    });
    formData.append("lat", latInput);
    formData.append("lon", lonInput);

    try {
      const res = await fetch(`${API_BASE}/api/upload/image`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setImageResults(data);
        setSelectedResultIdx(0);
        fetchAnalytics();
        fetchHistory();
      }
    } catch (err) {
      console.error("Image upload failed:", err);
    } finally {
      setUploadingImages(false);
    }
  };

  // Handle Video Upload
  const handleVideoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setVideoFile(file);
    setVideoStatus('uploading');
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lat", latInput);
    formData.append("lon", lonInput);

    try {
      const res = await fetch(`${API_BASE}/api/upload/video`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setVideoScanId(data.scan_id);
        setVideoStatus('processing');
        setVideoProgress(0);
      }
    } catch (e) {
      console.error("Video upload failed:", e);
      setVideoStatus('failed');
    }
  };

  // Start Live Webcam Detections
  const startWebcam = async () => {
    setWebcamActive(true);
    setLivePotholes([]);
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          currentGPS.current = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        },
        () => console.log("Using default fallback GPS coords")
      );
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      webcamInterval.current = setInterval(async () => {
        if (!videoRef.current || !canvasRef.current) return;
        
        const canvas = canvasRef.current;
        const video = videoRef.current;
        const ctx = canvas.getContext('2d');
        
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(async (blob) => {
          const formData = new FormData();
          formData.append("files", blob, "webcam_frame.jpg");
          formData.append("lat", currentGPS.current.lat);
          formData.append("lon", currentGPS.current.lon);

          try {
            const res = await fetch(`${API_BASE}/api/upload/image`, {
              method: "POST",
              body: formData
            });
            if (res.ok) {
              const data = await res.json();
              if (data && data.length > 0) {
                const det = data[0].detections;
                setLivePotholes(det);
                
                const minor = det.filter(d => d.severity === 'MINOR').length;
                const moderate = det.filter(d => d.severity === 'MODERATE').length;
                const severe = det.filter(d => d.severity === 'SEVERE').length;
                
                let label = 'GOOD';
                let color = 'var(--color-minor)';
                let alert = 'Optimal Road Profile - No Action Required';
                
                if (severe > 0) {
                  label = 'CRITICAL';
                  color = 'var(--color-severe)';
                  alert = 'CRITICAL SEVERITY - High collision risk ahead!';
                } else if (moderate > 0) {
                  label = 'WARNING';
                  color = 'var(--color-moderate)';
                  alert = 'WARNING - Medium potholes detected';
                } else if (minor > 0) {
                  label = 'MINOR';
                  color = 'var(--color-minor)';
                  alert = 'Safe - Minor pavement degradation';
                }
                setLiveCondition({ label, color, alert });
              }
            }
          } catch (e) {
            console.error("Frame evaluation failed:", e);
          }
        }, "image/jpeg", 0.75);
      }, 450);

    } catch (err) {
      console.error("Webcam session failed:", err);
      setWebcamActive(false);
    }
  };

  const stopWebcam = () => {
    setWebcamActive(false);
    clearInterval(webcamInterval.current);
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
  };

  const handleDeleteScan = async (id) => {
    if (confirm("Are you sure you want to permanently delete this telemetry scan?")) {
      try {
        const res = await fetch(`${API_BASE}/api/scans/${id}`, { method: "DELETE" });
        if (res.ok) {
          fetchHistory();
          fetchAnalytics();
          if (activeScanDetail && activeScanDetail.scan._id === id) {
            setActiveScanDetail(null);
          }
        }
      } catch (e) {
        console.error(e);
      }
    }
  };

  const showScanDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/scans/${id}`);
      if (res.ok) {
        const data = await res.json();
        if (data.scan && data.scan.scan_type === 'video') {
          setActiveTab('video');
          setVideoStatus('completed');
          setVideoResult(data);
        } else {
          setActiveScanDetail(data);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRerunScan = async (id, scanType = 'video') => {
    try {
      setActiveScanDetail(null);
      if (scanType === 'image') {
        setUploadingImages(true);
        setImageResults([]);
        setActiveTab('image');
        
        const res = await fetch(`${API_BASE}/api/scans/${id}/rerun`, {
          method: "POST"
        });
        if (res.ok) {
          const result = await res.json();
          setImageResults([result.data]);
          setSelectedResultIdx(0);
          fetchAnalytics();
          fetchHistory();
        } else {
          throw new Error("Failed to rerun image scan");
        }
        setUploadingImages(false);
      } else {
        setVideoScanId(id);
        setVideoStatus('processing');
        setVideoProgress(0);
        setVideoResult(null);
        setVideoFile(null);
        setActiveTab('video');

        const res = await fetch(`${API_BASE}/api/scans/${id}/rerun`, {
          method: "POST"
        });
        
        if (!res.ok) {
          throw new Error("Failed to start video scan rerun");
        }
      }
    } catch (e) {
      console.error("Failed to rerun scan:", e);
      if (scanType === 'image') {
        setUploadingImages(false);
      } else {
        setVideoStatus('failed');
        setVideoScanId(null);
      }
    }
  };

  // --- REAL DATA ADVANCED ANALYTICS CALCULATIONS ---
  
  // 1. Confidence Distribution (Recharts BarChart)
  const getConfidenceDistribution = () => {
    const buckets = { '50-60%': 0, '60-70%': 0, '70-80%': 0, '80-90%': 0, '90-100%': 0 };
    const coords = stats.coordinates || [];
    if (coords.length === 0) return [];
    
    coords.forEach(coord => {
      const conf = (coord.confidence || 0) * 100;
      if (conf >= 90) buckets['90-100%']++;
      else if (conf >= 80) buckets['80-90%']++;
      else if (conf >= 70) buckets['70-80%']++;
      else if (conf >= 60) buckets['60-70%']++;
      else if (conf >= 50) buckets['50-60%']++;
    });
    return Object.keys(buckets).map(key => ({ range: key, count: buckets[key] }));
  };

  // 2. Pothole Width Distribution (Recharts AreaChart)
  const getWidthDistribution = () => {
    const buckets = { '<20cm': 0, '20-40cm': 0, '40-60cm': 0, '60-80cm': 0, '>80cm': 0 };
    const coords = stats.coordinates || [];
    if (coords.length === 0) return [];

    coords.forEach(coord => {
      const w = coord.width_cm || 0;
      if (w < 20) buckets['<20cm']++;
      else if (w < 40) buckets['20-40cm']++;
      else if (w < 60) buckets['40-60cm']++;
      else if (w < 80) buckets['60-80cm']++;
      else buckets['>80cm']++;
    });
    return Object.keys(buckets).map(key => ({ size: key, count: buckets[key] }));
  };

  // 3. FPS Timeline performance metrics (Recharts Line/AreaChart)
  const getFPSTimeline = () => {
    const videoScans = scans.filter(s => s.scan_type === 'video' && s.avg_fps > 0);
    if (videoScans.length === 0) return [];
    return videoScans.slice(0, 10).reverse().map(s => ({
      name: s.scan_name.length > 12 ? s.scan_name.slice(0, 10) + '...' : s.scan_name,
      fps: s.avg_fps,
      latency: s.avg_processing_time_ms || 0
    }));
  };

  // 4. Severity Frequency Split calculations
  const totalHazards = stats.total_potholes || 0;
  const minorFreq = totalHazards ? ((stats.minor / totalHazards) * 100).toFixed(1) : 0;
  const moderateFreq = totalHazards ? ((stats.moderate / totalHazards) * 100).toFixed(1) : 0;
  const severeFreq = totalHazards ? ((stats.severe / totalHazards) * 100).toFixed(1) : 0;

  const pieData = [
    { name: 'Minor', value: stats.minor || 0, color: 'var(--color-minor)' },
    { name: 'Moderate', value: stats.moderate || 0, color: 'var(--color-moderate)' },
    { name: 'Severe', value: stats.severe || 0, color: 'var(--color-severe)' },
  ];

  const confidenceDistData = getConfidenceDistribution();
  const widthDistData = getWidthDistribution();
  const fpsTimelineData = getFPSTimeline();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', gap: 0 }}>
      
      {/* ─── SIDEBAR NAVIGATION (Linear.app Collapsible Style) ─── */}
      <aside className="glass-panel" style={{
        width: sidebarCollapsed ? '70px' : '260px',
        margin: '16px 12px 16px 16px',
        padding: '20px 14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        height: 'calc(100vh - 32px)',
        position: 'sticky',
        top: '16px',
        zIndex: 10,
        transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)'
      }}>
        {/* Sidebar Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: sidebarCollapsed ? 'center' : 'space-between', minHeight: '38px' }}>
          {!sidebarCollapsed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Brain style={{ color: 'var(--color-cyan)' }} size={24} className="pulse-glow" />
              <div>
                <h1 style={{ fontSize: '15px', fontWeight: '700', tracking: 'tight' }}>PAVEMIND AI</h1>
                <span style={{ fontSize: '9px', color: '#64748b', letterSpacing: '0.5px' }}>ROAD INTEL ENGINE</span>
              </div>
            </div>
          )}
          {sidebarCollapsed && <Brain style={{ color: 'var(--color-cyan)' }} size={24} className="pulse-glow" />}
          
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)',
              borderRadius: '6px', padding: '4px', cursor: 'pointer', color: '#94a3b8',
              marginLeft: sidebarCollapsed ? '0' : '8px'
            }}
          >
            {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>

        {/* Sidebar Navigation */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flexGrow: 1 }}>
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`sidebar-nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            title="Dashboard Overview"
            style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
          >
            <Activity size={16} /> {!sidebarCollapsed && <span>Dashboard Overview</span>}
          </button>
          
          <button 
            onClick={() => setActiveTab('image')}
            className={`sidebar-nav-btn ${activeTab === 'image' ? 'active' : ''}`}
            title="Image Analyzer"
            style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
          >
            <ImageIcon size={16} /> {!sidebarCollapsed && <span>Image Analyzer</span>}
          </button>

          <button 
            onClick={() => setActiveTab('video')}
            className={`sidebar-nav-btn ${activeTab === 'video' ? 'active' : ''}`}
            title="Video Tracking"
            style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
          >
            <Video size={16} /> {!sidebarCollapsed && <span>Video Tracking</span>}
          </button>

          <button 
            onClick={() => { setActiveTab('webcam'); startWebcam(); }}
            className={`sidebar-nav-btn ${activeTab === 'webcam' ? 'active' : ''}`}
            title="Live Scanner feed"
            style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
          >
            <Camera size={16} /> {!sidebarCollapsed && <span>Live Scanner Feed</span>}
          </button>

          <button 
            onClick={() => { setActiveTab('history'); fetchHistory(); }}
            className={`sidebar-nav-btn ${activeTab === 'history' ? 'active' : ''}`}
            title="Scans Database"
            style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
          >
            <History size={16} /> {!sidebarCollapsed && <span>Scans Database</span>}
          </button>
        </nav>

        {/* --- GEOLOCATION SETTING PANEL --- */}
        {!sidebarCollapsed && (
          <div className="glass-card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '10px', color: '#64748b', fontWeight: '700', letterSpacing: '0.05em' }}>DEFAULT SCAN LOCALE</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justify: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '10px', color: '#64748b' }}>Latitude</label>
                <input 
                  type="number" 
                  value={latInput} 
                  onChange={e => setLatInput(parseFloat(e.target.value))} 
                  className="fintech-input"
                  style={{ width: '80px', padding: '2px 4px', fontSize: '11px' }}
                />
              </div>
              <div style={{ display: 'flex', justify: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '10px', color: '#64748b' }}>Longitude</label>
                <input 
                  type="number" 
                  value={lonInput} 
                  onChange={e => setLonInput(parseFloat(e.target.value))} 
                  className="fintech-input"
                  style={{ width: '80px', padding: '2px 4px', fontSize: '11px' }}
                />
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* ─── MAIN CONTENT CONTAINER ─── */}
      <main style={{ flexGrow: 1, padding: '16px 16px 16px 4px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
        
        {/* --- HEADER --- */}
        <header className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 24px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '600' }}>Road Pothole Detection & Severity Analytics</h2>
            <p style={{ fontSize: '11px', color: '#64748b' }}>Enterprise infrastructure scanning dashboard with computer vision evaluation</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {dbConnected ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.15)', color: 'var(--color-minor)', padding: '4px 10px', borderRadius: '20px', fontSize: '10.5px', fontWeight: '600' }}>
                <Database size={10} /> Atlas MongoDB Node Connected
              </span>
            ) : (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.15)', color: 'var(--color-moderate)', padding: '4px 10px', borderRadius: '20px', fontSize: '10.5px', fontWeight: '600' }}>
                Standalone Local Storage Mode
              </span>
            )}
            <button 
              onClick={() => setTheme(theme === 'dark' ? 'ivory' : 'dark')} 
              title={`Switch to ${theme === 'dark' ? 'Ivory' : 'Dark'} Theme`}
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '5px', color: '#94a3b8', cursor: 'pointer' }}
            >
              {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
            </button>
            <button onClick={fetchAnalytics} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '5px', color: '#94a3b8', cursor: 'pointer' }}>
              <RefreshCw size={13} />
            </button>
          </div>
        </header>

        {/* ─── DASHBOARD TAB ─── */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {loadingStats ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '80px' }}><Loader2 className="pulse-glow" style={{ color: 'var(--color-cyan)' }} size={24} /></div>
            ) : (
              <>
                {/* Stripe-inspired KPI Cards */}
                <div className="dashboard-grid">
                  <div className={`gradient-kpi-card ${maximizedCard === 'avg-health' ? 'card-maximized' : ''}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', letterSpacing: '0.05em' }}>AVERAGE ROAD HEALTH</span>
                      {renderMaximizeButton('avg-health')}
                    </div>
                    <div style={{ 
                      fontSize: maximizedCard === 'avg-health' ? '120px' : '28px', 
                      fontWeight: '700', 
                      marginTop: '6px', 
                      textAlign: maximizedCard === 'avg-health' ? 'center' : 'left',
                      color: stats.avg_health_score > 75 ? 'var(--color-minor)' : (stats.avg_health_score > 50 ? 'var(--color-moderate)' : 'var(--color-severe)'),
                      textShadow: maximizedCard === 'avg-health' ? '0 0 40px currentColor' : 'none'
                    }}>
                      {stats.avg_health_score}%
                    </div>
                    <span style={{ 
                      fontSize: maximizedCard === 'avg-health' ? '20px' : '10px', 
                      color: '#64748b',
                      textAlign: maximizedCard === 'avg-health' ? 'center' : 'left',
                      marginTop: maximizedCard === 'avg-health' ? '20px' : '0',
                      display: 'block'
                    }}>
                      {stats.avg_health_score > 75 ? 'Pavement structure stable' : (stats.avg_health_score > 50 ? 'Medium scan warnings active' : 'Critical structural patches required')}
                    </span>
                  </div>

                  <div className={`gradient-kpi-card ${maximizedCard === 'completed-scans' ? 'card-maximized' : ''}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', letterSpacing: '0.05em' }}>COMPLETED SCANS</span>
                      {renderMaximizeButton('completed-scans')}
                    </div>
                    <div style={{ 
                      fontSize: maximizedCard === 'completed-scans' ? '120px' : '28px', 
                      fontWeight: '700', 
                      marginTop: '6px', 
                      textAlign: maximizedCard === 'completed-scans' ? 'center' : 'left',
                      color: 'var(--text-header)',
                      textShadow: maximizedCard === 'completed-scans' ? '0 0 40px rgba(255,255,255,0.3)' : 'none'
                    }}>
                      {stats.total_scans}
                    </div>
                    <span style={{ 
                      fontSize: maximizedCard === 'completed-scans' ? '20px' : '10px', 
                      color: '#64748b',
                      textAlign: maximizedCard === 'completed-scans' ? 'center' : 'left',
                      marginTop: maximizedCard === 'completed-scans' ? '20px' : '0',
                      display: 'block'
                    }}>Total stored video and image sessions</span>
                  </div>

                  <div className={`gradient-kpi-card ${maximizedCard === 'anomalies' ? 'card-maximized' : ''}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', letterSpacing: '0.05em' }}>ANOMALIES REGISTERED</span>
                      {renderMaximizeButton('anomalies')}
                    </div>
                    <div style={{ 
                      fontSize: maximizedCard === 'anomalies' ? '120px' : '28px', 
                      fontWeight: '700', 
                      marginTop: '6px', 
                      textAlign: maximizedCard === 'anomalies' ? 'center' : 'left',
                      color: 'var(--color-cyan)',
                      textShadow: maximizedCard === 'anomalies' ? '0 0 40px var(--color-cyan)' : 'none'
                    }}>
                      {stats.total_potholes}
                    </div>
                    <span style={{ 
                      fontSize: maximizedCard === 'anomalies' ? '20px' : '10px', 
                      color: '#64748b',
                      textAlign: maximizedCard === 'anomalies' ? 'center' : 'left',
                      marginTop: maximizedCard === 'anomalies' ? '20px' : '0',
                      display: 'block'
                    }}>Total detected anomalies</span>
                  </div>

                  <div className={`gradient-kpi-card ${maximizedCard === 'severe-threats' ? 'card-maximized' : ''}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', letterSpacing: '0.05em' }}>SEVERE THREATS</span>
                      {renderMaximizeButton('severe-threats')}
                    </div>
                    <div style={{ 
                      fontSize: maximizedCard === 'severe-threats' ? '120px' : '28px', 
                      fontWeight: '700', 
                      marginTop: '6px', 
                      textAlign: maximizedCard === 'severe-threats' ? 'center' : 'left',
                      color: 'var(--color-severe)',
                      textShadow: maximizedCard === 'severe-threats' ? '0 0 40px var(--color-severe)' : 'none'
                    }}>
                      {stats.severe}
                    </div>
                    <span style={{ 
                      fontSize: maximizedCard === 'severe-threats' ? '20px' : '10px', 
                      color: '#64748b',
                      textAlign: maximizedCard === 'severe-threats' ? 'center' : 'left',
                      marginTop: maximizedCard === 'severe-threats' ? '20px' : '0',
                      display: 'block'
                    }}>Critical potholes (width &gt; 70cm)</span>
                  </div>
                </div>

                {/* KPI Charts Row */}
                <div style={{ display: maximizedCard === 'trends-chart' || maximizedCard === 'categories-pie' ? 'block' : 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '16px' }}>
                  
                  {/* Trends Chart */}
                  <div className={`glass-panel ${maximizedCard === 'trends-chart' ? 'card-maximized' : ''}`} style={{ padding: '16px', display: maximizedCard === 'categories-pie' ? 'none' : 'block' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <TrendingUp size={14} style={{ color: 'var(--color-cyan)' }} />
                        <h3 style={{ fontSize: '13px', fontWeight: '600' }}>SEVERITY TRENDS (LAST 10 SCANS)</h3>
                      </div>
                      {renderMaximizeButton('trends-chart')}
                    </div>
                    {(!stats.trends || stats.trends.length === 0) ? (
                      <div className="fallback-placeholder" style={{ height: maximizedCard === 'trends-chart' ? '70vh' : '220px' }}>No Data Available</div>
                    ) : (
                      <div style={{ width: '100%', height: maximizedCard === 'trends-chart' ? '70vh' : '220px' }}>
                        <ResponsiveContainer>
                          <AreaChart data={stats.trends}>
                            <defs>
                              <linearGradient id="colorMinor" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-minor)" stopOpacity={0.2}/>
                                <stop offset="95%" stopColor="var(--color-minor)" stopOpacity={0}/>
                              </linearGradient>
                              <linearGradient id="colorModerate" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-moderate)" stopOpacity={0.2}/>
                                <stop offset="95%" stopColor="var(--color-moderate)" stopOpacity={0}/>
                              </linearGradient>
                              <linearGradient id="colorSevere" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-severe)" stopOpacity={0.2}/>
                                <stop offset="95%" stopColor="var(--color-severe)" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <XAxis dataKey="name" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <YAxis stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-primary)' }} />
                            <Area type="monotone" dataKey="minor" stroke="var(--color-minor)" fillOpacity={1} fill="url(#colorMinor)" strokeWidth={1.5} />
                            <Area type="monotone" dataKey="moderate" stroke="var(--color-moderate)" fillOpacity={1} fill="url(#colorModerate)" strokeWidth={1.5} />
                            <Area type="monotone" dataKey="severe" stroke="var(--color-severe)" fillOpacity={1} fill="url(#colorSevere)" strokeWidth={1.5} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>

                  {/* Severity Distribution Pie Chart */}
                  <div className={`glass-panel ${maximizedCard === 'categories-pie' ? 'card-maximized' : ''}`} style={{ padding: '16px', display: maximizedCard === 'trends-chart' ? 'none' : 'block' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <PieIcon size={14} style={{ color: 'var(--color-cyan)' }} />
                        <h3 style={{ fontSize: '13px', fontWeight: '600' }}>SEVERITY CATEGORIES DISTRIBUTION</h3>
                      </div>
                      {renderMaximizeButton('categories-pie')}
                    </div>
                    {(stats.minor === 0 && stats.moderate === 0 && stats.severe === 0) ? (
                      <div className="fallback-placeholder" style={{ height: maximizedCard === 'categories-pie' ? '70vh' : '220px' }}>No Data Available</div>
                    ) : (
                      <div style={{ width: '100%', height: maximizedCard === 'categories-pie' ? '70vh' : '220px', display: 'flex', justifyContent: 'center' }}>
                        <ResponsiveContainer>
                          <PieChart>
                            <Pie
                              data={pieData}
                              cx="50%"
                              cy="50%"
                              innerRadius={50}
                              outerRadius={70}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {pieData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-primary)' }} />
                            <Legend layout="horizontal" align="center" verticalAlign="bottom" iconType="circle" style={{ fontSize: '11px' }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                </div>

                {/* --- ADVANCED ANALYTICS SECTION --- */}
                <div style={{ 
                  display: maximizedCard === 'confidence-dist' || maximizedCard === 'width-dist' || maximizedCard === 'fps-timeline' ? 'block' : 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', 
                  gap: '16px' 
                }}>
                  
                  {/* Panel 1: Confidence Distribution */}
                  <div className={`glass-panel ${maximizedCard === 'confidence-dist' ? 'card-maximized' : ''}`} style={{ 
                    padding: '16px',
                    display: (maximizedCard && maximizedCard !== 'confidence-dist') ? 'none' : 'block'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <BarChart3 size={14} style={{ color: 'var(--color-purple)' }} />
                        <h3 style={{ fontSize: '13px', fontWeight: '600' }}>CONFIDENCE RATING DISTRIBUTION</h3>
                      </div>
                      {renderMaximizeButton('confidence-dist')}
                    </div>
                    {confidenceDistData.length === 0 ? (
                      <div className="fallback-placeholder" style={{ height: maximizedCard === 'confidence-dist' ? '70vh' : '180px' }}>No Data Available</div>
                    ) : (
                      <div style={{ width: '100%', height: maximizedCard === 'confidence-dist' ? '70vh' : '180px' }}>
                        <ResponsiveContainer>
                          <BarChart data={confidenceDistData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.03)'} vertical={false} />
                            <XAxis dataKey="range" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <YAxis stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-primary)' }} />
                            <Bar dataKey="count" fill="var(--color-purple)" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>

                  {/* Panel 2: Pothole Width Distribution */}
                  <div className={`glass-panel ${maximizedCard === 'width-dist' ? 'card-maximized' : ''}`} style={{ 
                    padding: '16px',
                    display: (maximizedCard && maximizedCard !== 'width-dist') ? 'none' : 'block'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Ruler size={14} style={{ color: 'var(--color-cyan)' }} />
                        <h3 style={{ fontSize: '13px', fontWeight: '600' }}>POTHOLE WIDTH SPECS DISTRIBUTION</h3>
                      </div>
                      {renderMaximizeButton('width-dist')}
                    </div>
                    {widthDistData.length === 0 ? (
                      <div className="fallback-placeholder" style={{ height: maximizedCard === 'width-dist' ? '70vh' : '180px' }}>No Data Available</div>
                    ) : (
                      <div style={{ width: '100%', height: maximizedCard === 'width-dist' ? '70vh' : '180px' }}>
                        <ResponsiveContainer>
                          <AreaChart data={widthDistData}>
                            <defs>
                              <linearGradient id="colorWidth" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-cyan)" stopOpacity={0.2}/>
                                <stop offset="95%" stopColor="var(--color-cyan)" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.03)'} vertical={false} />
                            <XAxis dataKey="size" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <YAxis stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-primary)' }} />
                            <Area type="monotone" dataKey="count" stroke="var(--color-cyan)" fillOpacity={1} fill="url(#colorWidth)" strokeWidth={1.5} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>

                  {/* Panel 3: FPS Timeline Performance */}
                  <div className={`glass-panel ${maximizedCard === 'fps-timeline' ? 'card-maximized' : ''}`} style={{ 
                    padding: '16px',
                    display: (maximizedCard && maximizedCard !== 'fps-timeline') ? 'none' : 'block'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Activity size={14} style={{ color: 'var(--color-minor)' }} />
                        <h3 style={{ fontSize: '13px', fontWeight: '600' }}>SCAN FPS PERFORMANCE TIMELINE</h3>
                      </div>
                      {renderMaximizeButton('fps-timeline')}
                    </div>
                    {fpsTimelineData.length === 0 ? (
                      <div className="fallback-placeholder" style={{ height: maximizedCard === 'fps-timeline' ? '70vh' : '180px' }}>No Data Available</div>
                    ) : (
                      <div style={{ width: '100%', height: maximizedCard === 'fps-timeline' ? '70vh' : '180px' }}>
                        <ResponsiveContainer>
                          <AreaChart data={fpsTimelineData}>
                            <defs>
                              <linearGradient id="colorFps" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-minor)" stopOpacity={0.2}/>
                                <stop offset="95%" stopColor="var(--color-minor)" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.03)'} vertical={false} />
                            <XAxis dataKey="name" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={8} tickLine={false} />
                            <YAxis stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                            <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-primary)' }} />
                            <Area type="monotone" dataKey="fps" name="Processing FPS" stroke="var(--color-minor)" fillOpacity={1} fill="url(#colorFps)" strokeWidth={1.5} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                </div>

                {/* Panel 4: Severity Frequency Indicator Matrix */}
                <div className={`glass-panel ${maximizedCard === 'severity-matrix' ? 'card-maximized' : ''}`} style={{ 
                  padding: '16px',
                  display: (maximizedCard && maximizedCard !== 'severity-matrix') ? 'none' : 'block'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Layers size={14} style={{ color: 'var(--color-purple)' }} />
                      <h3 style={{ fontSize: '13px', fontWeight: '600' }}>SEVERITY RATIO FREQUENCY MATRIX</h3>
                    </div>
                    {renderMaximizeButton('severity-matrix')}
                  </div>
                  {totalHazards === 0 ? (
                    <div className="fallback-placeholder" style={{ padding: '20px' }}>No Data Available</div>
                  ) : (
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
                      gap: '12px',
                      height: maximizedCard === 'severity-matrix' ? '70vh' : 'auto',
                      alignContent: maximizedCard === 'severity-matrix' ? 'center' : 'stretch'
                    }}>
                      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: maximizedCard === 'severity-matrix' ? '40px' : '16px', alignItems: maximizedCard === 'severity-matrix' ? 'center' : 'stretch' }}>
                        <span style={{ fontSize: maximizedCard === 'severity-matrix' ? '18px' : '10px', color: '#64748b', fontWeight: '600' }}>MINOR ANOMALY FREQUENCY</span>
                        <div style={{ fontSize: maximizedCard === 'severity-matrix' ? '80px' : '20px', fontWeight: '700', color: 'var(--color-minor)' }}>{minorFreq}%</div>
                        <span style={{ fontSize: maximizedCard === 'severity-matrix' ? '18px' : '11px', color: '#64748b' }}>({stats.minor} of {totalHazards} points)</span>
                      </div>
                      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: maximizedCard === 'severity-matrix' ? '40px' : '16px', alignItems: maximizedCard === 'severity-matrix' ? 'center' : 'stretch' }}>
                        <span style={{ fontSize: maximizedCard === 'severity-matrix' ? '18px' : '10px', color: '#64748b', fontWeight: '600' }}>MODERATE HAZARD FREQUENCY</span>
                        <div style={{ fontSize: maximizedCard === 'severity-matrix' ? '80px' : '20px', fontWeight: '700', color: 'var(--color-moderate)' }}>{moderateFreq}%</div>
                        <span style={{ fontSize: maximizedCard === 'severity-matrix' ? '18px' : '11px', color: '#64748b' }}>({stats.moderate} of {totalHazards} points)</span>
                      </div>
                      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: maximizedCard === 'severity-matrix' ? '40px' : '16px', alignItems: maximizedCard === 'severity-matrix' ? 'center' : 'stretch' }}>
                        <span style={{ fontSize: maximizedCard === 'severity-matrix' ? '18px' : '10px', color: '#64748b', fontWeight: '600' }}>SEVERE CRITICAL FREQUENCY</span>
                        <div style={{ fontSize: maximizedCard === 'severity-matrix' ? '80px' : '20px', fontWeight: '700', color: 'var(--color-severe)' }}>{severeFreq}%</div>
                        <span style={{ fontSize: maximizedCard === 'severity-matrix' ? '18px' : '11px', color: '#64748b' }}>({stats.severe} of {totalHazards} points)</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Spatial Map Component */}
                <PotholeMap 
                  coordinates={stats.coordinates} 
                  theme={theme} 
                  latInput={latInput}
                  lonInput={lonInput}
                  setLatInput={setLatInput}
                  setLonInput={setLonInput}
                />
              </>
            )}
          </div>
        )}

        {/* ─── IMAGE ANALYZER TAB ─── */}
        {activeTab === 'image' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Image Uploader Panel */}
            {imageResults.length === 0 && (
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                {!uploadingImages ? (
                  <div style={{ border: '1px dashed rgba(255,255,255,0.08)', borderRadius: '12px', padding: '30px', width: '100%', textAlign: 'center', cursor: 'pointer', background: 'rgba(255,255,255,0.005)' }}>
                    <input 
                      type="file" 
                      multiple 
                      accept="image/*" 
                      onChange={handleImageUpload} 
                      id="image-input" 
                      style={{ display: 'none' }} 
                    />
                    <label htmlFor="image-input" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                      <ImageIcon size={36} style={{ color: 'var(--color-cyan)' }} />
                      <b style={{ fontSize: '14px', color: 'var(--text-header)' }}>Click to Import Road Images for Evaluation</b>
                      <span style={{ fontSize: '11.5px', color: '#64748b' }}>Supports standard JPEG, JPG, and PNG files</span>
                    </label>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12.5px' }}>
                    <Loader2 className="pulse-glow" style={{ color: 'var(--color-cyan)' }} size={16} />
                    <span>Optical analysis model processing frames...</span>
                  </div>
                )}
              </div>
            )}

            {/* Image Detections Result Grid */}
            {imageResults.length > 0 && (
              <div 
                ref={imageContainerRef}
                style={{ 
                  display: 'flex', 
                  width: '100%', 
                  position: 'relative', 
                  gap: 0,
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  background: 'rgba(13, 19, 33, 0.2)'
                }}
              >
                {/* Uploaded List */}
                <div 
                  style={{ 
                    width: `${imagePanelWidth}%`, 
                    padding: '12px', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: '6px',
                    minWidth: '150px',
                    flexShrink: 0,
                    boxSizing: 'border-box'
                  }}
                >
                  <h3 style={{ fontSize: '11px', color: '#64748b', borderBottom: '1px solid var(--border-color)', paddingBottom: '6px', fontWeight: '700' }}>SESSIONS ACTIVE</h3>
                  {imageResults.map((result, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedResultIdx(idx)}
                      style={{
                        padding: '8px 10px', border: 0, borderRadius: '6px', background: selectedResultIdx === idx ? 'rgba(255,255,255,0.04)' : 'transparent',
                        color: selectedResultIdx === idx ? 'var(--text-header)' : '#64748b', fontSize: '12.5px', cursor: 'pointer', textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: selectedResultIdx === idx ? '600' : '400'
                      }}
                    >
                      {result.scan_name}
                    </button>
                  ))}
                </div>

                {/* Split Resizer bar */}
                <div
                  onMouseDown={handleImageMouseDown}
                  style={{
                    width: '6px',
                    cursor: 'col-resize',
                    background: isImageResizing ? 'var(--color-cyan)' : 'rgba(255, 255, 255, 0.05)',
                    alignSelf: 'stretch',
                    position: 'relative',
                    transition: 'background 0.1s',
                    zIndex: 10
                  }}
                  className="resize-handle"
                >
                  <div style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '2px',
                    height: '30px',
                    background: 'rgba(255,255,255,0.2)',
                    borderRadius: '1px'
                  }} />
                </div>

                {/* Selected File Details */}
                <div 
                  style={{ 
                    flexGrow: 1,
                    width: `${100 - imagePanelWidth}%`,
                    padding: '16px', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: '16px',
                    minWidth: '320px',
                    boxSizing: 'border-box',
                    overflow: 'hidden'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: '600' }}>{imageResults[selectedResultIdx].scan_name}</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <button
                        onClick={() => handleRerunScan(imageResults[selectedResultIdx].scan_id || imageResults[selectedResultIdx]._id, 'image')}
                        className="fintech-btn"
                        style={{ background: 'rgba(6,182,212,0.1)', borderColor: 'rgba(6,182,212,0.2)', color: 'var(--color-cyan)', fontSize: '12px', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <RefreshCw size={12} /> RESCAN IMAGE
                      </button>
                      <button
                        onClick={() => {
                          setImageResults([]);
                          setSelectedResultIdx(0);
                        }}
                        className="fintech-btn fintech-btn-secondary"
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                      >
                        Upload New Image
                      </button>
                      <span style={{ 
                        background: imageResults[selectedResultIdx].road_health_score > 75 ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                        border: `1px solid ${imageResults[selectedResultIdx].road_health_score > 75 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}`,
                        color: imageResults[selectedResultIdx].road_health_score > 75 ? 'var(--color-minor)' : 'var(--color-severe)',
                        padding: '6px 12px', borderRadius: '12px', fontSize: '11px', fontWeight: '600'
                      }}>
                        Road Safety Index: {imageResults[selectedResultIdx].road_health_score}%
                      </span>
                    </div>
                  </div>

                  {/* Side by Side Images */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <span style={{ fontSize: '10.5px', color: '#64748b', display: 'block', marginBottom: '6px' }}>SOURCE FRAME</span>
                      <img 
                        src={`${API_BASE}${imageResults[selectedResultIdx].input_url}`} 
                        alt="Original" 
                        style={{ width: '100%', borderRadius: '10px', border: '1px solid var(--border-color)' }} 
                      />
                    </div>
                    <div>
                      <span style={{ fontSize: '10.5px', color: '#64748b', display: 'block', marginBottom: '6px' }}>SEVERITY ANOMALIES MAPPED</span>
                      <div style={{ position: 'relative' }}>
                        <div className="optical-scan-bar" />
                        <img 
                          src={`${API_BASE}${imageResults[selectedResultIdx].output_url}?t=${imageResults[selectedResultIdx].date ? encodeURIComponent(imageResults[selectedResultIdx].date) : Date.now()}`} 
                          alt="Detections" 
                          style={{ width: '100%', borderRadius: '10px', border: '1px solid var(--border-color)' }} 
                        />
                      </div>
                    </div>
                  </div>

                  {/* Bounding Box Metrics */}
                  <div className="glass-card">
                    <h4 style={{ fontSize: '12.5px', marginBottom: '8px', fontWeight: '600' }}>ANOMALY METRICS OVERVIEW</h4>
                    {imageResults[selectedResultIdx].detections.length === 0 ? (
                      <span style={{ fontSize: '12px', color: '#64748b' }}>No structural anomalies detected. Infrastructure profile is clear.</span>
                    ) : (
                      <table className="fintech-table">
                        <thead>
                          <tr>
                            <th>SEVERITY LEVEL</th>
                            <th>ESTIMATED WIDTH</th>
                            <th>ESTIMATED HEIGHT</th>
                            <th>CAMERA DISTANCE</th>
                            <th>PROBABILITY RATIO</th>
                          </tr>
                        </thead>
                        <tbody>
                          {imageResults[selectedResultIdx].detections.map((det, dIdx) => (
                            <tr key={dIdx}>
                              <td>
                                <span className={`severity-pill ${det.severity === 'SEVERE' ? 'severity-pill-severe' : (det.severity === 'MODERATE' ? 'severity-pill-moderate' : 'severity-pill-minor')}`}>
                                  <span className="severity-dot">
                                    <span className="severity-dot-pulse" />
                                  </span>
                                  {det.severity}
                                </span>
                              </td>
                              <td>{det.width_cm ? `${det.width_cm.toFixed(1)} cm` : 'N/A'}</td>
                              <td>{det.height_cm ? `${det.height_cm.toFixed(1)} cm` : 'N/A'}</td>
                              <td>{det.distance_m ? `${det.distance_m.toFixed(2)} m` : 'N/A'}</td>
                              <td className="mono-font">{(det.confidence * 100).toFixed(0)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── VIDEO TRACKING TAB ─── */}
        {activeTab === 'video' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Video Uploader & Progress Panel */}
            {(!videoStatus || videoStatus === 'uploading' || videoStatus === 'processing' || videoStatus === 'failed') && (
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                {(!videoStatus || videoStatus === 'failed') && (
                  <div style={{ border: '1px dashed rgba(255,255,255,0.08)', borderRadius: '12px', padding: '30px', width: '100%', textAlign: 'center', cursor: 'pointer', background: 'rgba(255,255,255,0.005)' }}>
                    <input 
                      type="file" 
                      accept="video/*" 
                      onChange={handleVideoUpload} 
                      id="video-input" 
                      style={{ display: 'none' }} 
                    />
                    <label htmlFor="video-input" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                      <Video size={36} style={{ color: 'var(--color-cyan)' }} />
                      <b style={{ fontSize: '14px', color: 'var(--text-header)' }}>Click to Import Road Video Stream</b>
                      <span style={{ fontSize: '11.5px', color: '#64748b' }}>Supports FSD / road scans (MP4, AVI, MOV formats)</span>
                    </label>
                  </div>
                )}

                {/* Uploading Status */}
                {videoStatus === 'uploading' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12.5px' }}>
                    <Loader2 className="pulse-glow" style={{ color: 'var(--color-cyan)' }} size={16} />
                    <span>Buffering video stream to segment directories...</span>
                  </div>
                )}

                {/* Processing Progress */}
                {videoStatus === 'processing' && (
                  <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12.5px' }}>
                      <Loader2 className="pulse-glow" style={{ color: 'var(--color-cyan)' }} size={16} />
                      <span>Neural Object evaluation model active...</span>
                    </div>
                    <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${videoProgress}%`, height: '100%', background: 'var(--color-cyan)', boxShadow: '0 0 8px var(--color-cyan)' }} />
                    </div>
                    <span style={{ fontSize: '10.5px', color: '#64748b', fontFamily: 'JetBrains Mono' }}>{videoProgress}% COMPLETE</span>
                  </div>
                )}
              </div>
            )}

            {/* Video Processing Output */}
            {videoStatus === 'completed' && videoResult && (
              <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ fontSize: '14px', fontWeight: '600' }}>Processed Video Output</h3>
                    <p style={{ fontSize: '11.5px', color: '#64748b' }}>
                      Scan Name: <b>{videoResult.scan.scan_name}</b> | Registered Potholes: <b style={{ color: 'var(--color-cyan)' }}>{videoResult.scan.total_potholes}</b> | Rate: <b style={{ color: 'var(--color-purple)' }}>{videoResult.scan.avg_fps} FPS</b>
                    </p>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button
                      onClick={() => handleRerunScan(videoResult.scan._id)}
                      className="fintech-btn"
                      style={{ background: 'rgba(6,182,212,0.1)', borderColor: 'rgba(6,182,212,0.2)', color: 'var(--color-cyan)', fontSize: '12px', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <RefreshCw size={12} /> RERUN SCAN
                    </button>
                    <button
                      onClick={() => {
                        setVideoFile(null);
                        setVideoStatus(null);
                        setVideoResult(null);
                      }}
                      className="fintech-btn fintech-btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 12px' }}
                    >
                      Upload New Video
                    </button>
                    <a 
                      href={`${API_BASE}/api/download/${videoResult.scan._id}`}
                      className="fintech-btn"
                      style={{ textDecoration: 'none', fontSize: '12px', padding: '6px 12px' }}
                    >
                      <Download size={13} style={{ marginRight: '4px' }} /> DOWNLOAD ZIP REPORT
                    </a>
                  </div>
                </div>

                <div 
                  ref={containerRef}
                  style={{ 
                    display: 'flex', 
                    width: '100%', 
                    position: 'relative', 
                    gap: 0,
                    border: '1px solid var(--border-color)',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    background: 'rgba(13, 19, 33, 0.2)'
                  }}
                >
                  {/* Left Panel: Video Player, Custom Seeker & Fullscreen controls */}
                  <div 
                    style={{ 
                      width: `${videoPanelWidth}%`, 
                      padding: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      minWidth: '320px',
                      flexShrink: 0
                    }}
                  >
                    <div style={{ position: 'relative', width: '100%', background: '#000', borderRadius: '10px', overflow: 'hidden' }}>
                      <video 
                        ref={processedVideoRef}
                        key={`${videoResult.scan._id}_video`}
                        src={`${API_BASE}${videoResult.scan.output_video_url}?t=${videoCacheBuster}`}
                        controls
                        style={{ width: '100%', display: 'block' }}
                        onTimeUpdate={(e) => setVideoTime(e.target.currentTime)}
                        onDurationChange={(e) => setVideoDuration(e.target.duration)}
                        onLoadedMetadata={(e) => setVideoDuration(e.target.duration)}
                      />
                      {/* Native Fullscreen overlay button */}
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          if (processedVideoRef.current) {
                            if (processedVideoRef.current.requestFullscreen) {
                              processedVideoRef.current.requestFullscreen();
                            } else if (processedVideoRef.current.webkitRequestFullscreen) {
                              processedVideoRef.current.webkitRequestFullscreen();
                            }
                          }
                        }}
                        style={{
                          position: 'absolute',
                          top: '12px',
                          right: '12px',
                          background: 'rgba(13,19,33,0.7)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '6px',
                          padding: '6px',
                          color: 'var(--text-header)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          zIndex: 8
                        }}
                        title="Fullscreen Video"
                      >
                        <Maximize size={14} />
                      </button>
                    </div>

                    {/* Detection Timeline Representation Bar */}
                    <div style={{ marginTop: '16px' }}>
                      <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', display: 'block', marginBottom: '8px' }}>
                        DETECTION TIMELINE MAPPER (CLICK TICK TO SEEK)
                      </span>
                      
                      <div 
                        onClick={(e) => {
                          if (!processedVideoRef.current || !videoDuration) return;
                          const rect = e.currentTarget.getBoundingClientRect();
                          const clickX = e.clientX - rect.left;
                          const clickPercent = clickX / rect.width;
                          processedVideoRef.current.currentTime = clickPercent * videoDuration;
                        }}
                        style={{ 
                          position: 'relative', 
                          width: '100%', 
                          height: '24px', 
                          background: 'rgba(255,255,255,0.03)', 
                          border: '1px solid rgba(255,255,255,0.06)',
                          borderRadius: '6px', 
                          cursor: 'pointer' 
                        }}
                      >
                        {/* Current play progress bar */}
                        <div style={{ 
                          position: 'absolute', 
                          top: 0, 
                          left: 0, 
                          height: '100%', 
                          width: `${videoDuration > 0 ? (videoTime / videoDuration) * 100 : 0}%`, 
                          background: 'rgba(6, 182, 212, 0.08)', 
                          borderRadius: '5px',
                          pointerEvents: 'none'
                        }} />

                        {/* Vertical current play head line */}
                        <div style={{
                          position: 'absolute',
                          top: 0,
                          bottom: 0,
                          left: `${videoDuration > 0 ? (videoTime / videoDuration) * 100 : 0}%`,
                          width: '2px',
                          background: 'var(--color-cyan)',
                          boxShadow: '0 0 6px var(--color-cyan)',
                          pointerEvents: 'none',
                          zIndex: 6
                        }} />

                        {/* Timeline detection markers */}
                        {videoResult.detections && videoResult.detections.map((det, idx) => {
                          const maxFrame = videoResult.detections.reduce((max, d) => Math.max(max, d.frame), 0) || 1;
                          const pct = (det.frame / maxFrame) * 100;
                          const color = det.severity === 'SEVERE' ? 'var(--color-severe)' : (det.severity === 'MODERATE' ? 'var(--color-moderate)' : 'var(--color-minor)');
                          const calculatedFPS = (videoDuration > 0 && maxFrame > 0) ? (maxFrame / videoDuration) : 25.0;
                          return (
                            <div 
                              key={idx}
                              className="timeline-marker"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (processedVideoRef.current) {
                                  processedVideoRef.current.currentTime = det.frame / calculatedFPS;
                                }
                              }}
                              style={{
                                position: 'absolute',
                                left: `${pct}%`,
                                top: '50%',
                                transform: 'translate(-50%, -50%)',
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                backgroundColor: color,
                                border: '1px solid #ffffff',
                                cursor: 'pointer',
                                zIndex: 5
                              }}
                            >
                              <div className="timeline-tooltip">
                                <div style={{ fontWeight: '700', marginBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '2px' }}>
                                  Frame #{det.frame}
                                </div>
                                <div>Severity: <span style={{ color, fontWeight: '700' }}>{det.severity}</span></div>
                                <div>Width: <b>{det.width_cm ? det.width_cm.toFixed(1) : 'N/A'} cm</b></div>
                                <div>Conf: <b>{(det.confidence * 100).toFixed(0)}%</b></div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '9.5px', color: '#64748b', fontFamily: 'JetBrains Mono' }}>
                        <span>0.0s</span>
                        <span>ACTIVE FRAME: {Math.round(videoTime * ((videoResult.detections.reduce((max, d) => Math.max(max, d.frame), 0) || 1) / (videoDuration || 1)))}</span>
                        <span>{videoDuration ? videoDuration.toFixed(1) : '0.0'}s</span>
                      </div>
                    </div>
                  </div>

                  {/* Split Resizer bar */}
                  <div
                    onMouseDown={handleMouseDown}
                    style={{
                      width: '6px',
                      cursor: 'col-resize',
                      background: isResizing ? 'var(--color-cyan)' : 'rgba(255, 255, 255, 0.05)',
                      alignSelf: 'stretch',
                      position: 'relative',
                      transition: 'background 0.1s',
                      zIndex: 10
                    }}
                    className="resize-handle"
                  >
                    <div style={{
                      position: 'absolute',
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '2px',
                      height: '30px',
                      background: 'rgba(255,255,255,0.2)',
                      borderRadius: '1px'
                    }} />
                  </div>

                  {/* Right Panel: Tabs side details */}
                  <div 
                    style={{ 
                      flexGrow: 1, 
                      width: `${100 - videoPanelWidth}%`,
                      padding: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      minWidth: '320px',
                      overflow: 'hidden'
                    }}
                  >
                    {/* Details Tabs Header */}
                    <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', marginBottom: '16px', gap: '8px' }}>
                      <button
                        onClick={() => setVideoDetailTab('events')}
                        className={`sidebar-nav-btn`}
                        style={{ 
                          width: 'auto', 
                          padding: '8px 16px', 
                          fontSize: '12px', 
                          borderRadius: '6px 6px 0 0',
                          borderBottom: videoDetailTab === 'events' ? '2px solid var(--color-cyan)' : 'none',
                          background: videoDetailTab === 'events' ? 'rgba(255,255,255,0.02)' : 'transparent',
                          color: videoDetailTab === 'events' ? 'var(--text-header)' : 'var(--text-muted)',
                          boxShadow: 'none'
                        }}
                      >
                        Live Events
                      </button>
                      <button
                        onClick={() => setVideoDetailTab('stats')}
                        className={`sidebar-nav-btn`}
                        style={{ 
                          width: 'auto', 
                          padding: '8px 16px', 
                          fontSize: '12px', 
                          borderRadius: '6px 6px 0 0',
                          borderBottom: videoDetailTab === 'stats' ? '2px solid var(--color-cyan)' : 'none',
                          background: videoDetailTab === 'stats' ? 'rgba(255,255,255,0.02)' : 'transparent',
                          color: videoDetailTab === 'stats' ? 'var(--text-header)' : 'var(--text-muted)',
                          boxShadow: 'none'
                        }}
                      >
                        Statistics
                      </button>
                      <button
                        onClick={() => setVideoDetailTab('reports')}
                        className={`sidebar-nav-btn`}
                        style={{ 
                          width: 'auto', 
                          padding: '8px 16px', 
                          fontSize: '12px', 
                          borderRadius: '6px 6px 0 0',
                          borderBottom: videoDetailTab === 'reports' ? '2px solid var(--color-cyan)' : 'none',
                          background: videoDetailTab === 'reports' ? 'rgba(255,255,255,0.02)' : 'transparent',
                          color: videoDetailTab === 'reports' ? 'var(--text-header)' : 'var(--text-muted)',
                          boxShadow: 'none'
                        }}
                      >
                        Exported Reports
                      </button>
                    </div>

                    {/* Tab 1: Live Events content */}
                    {videoDetailTab === 'events' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1, overflow: 'hidden' }}>
                        {/* Filters */}
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          <input
                            type="text"
                            placeholder="Search by ID, Severity, Width..."
                            value={eventSearch}
                            onChange={(e) => setEventSearch(e.target.value)}
                            className="fintech-input"
                            style={{ flexGrow: 1, padding: '6px 12px', fontSize: '12px', borderRadius: '6px' }}
                          />
                          <div style={{ display: 'flex', gap: '4px' }}>
                            {['MINOR', 'MODERATE', 'SEVERE'].map(sev => {
                              const active = eventSeverityFilter[sev];
                              const color = sev === 'SEVERE' ? 'var(--color-severe)' : (sev === 'MODERATE' ? 'var(--color-moderate)' : 'var(--color-minor)');
                              return (
                                <button
                                  key={sev}
                                  onClick={() => setEventSeverityFilter(prev => ({ ...prev, [sev]: !prev[sev] }))}
                                  style={{
                                    fontSize: '10px',
                                    padding: '4px 10px',
                                    borderRadius: '4px',
                                    border: `1px solid ${active ? color : 'rgba(255,255,255,0.06)'}`,
                                    background: active ? `rgba(${sev === 'SEVERE' ? '239,68,68' : (sev === 'MODERATE' ? '245,158,11' : '16,185,129')}, 0.08)` : 'transparent',
                                    color: active ? color : 'var(--text-muted)',
                                    cursor: 'pointer',
                                    fontWeight: '700'
                                  }}
                                >
                                  {sev}
                                </button>
                              );
                            })}
                          </div>
                        </div>

                        {/* Synchronized logs list */}
                        <div 
                          ref={logsContainerRef}
                          style={{ 
                            flexGrow: 1, 
                            overflowY: 'auto', 
                            maxHeight: '380px',
                            border: '1px solid var(--border-color)',
                            borderRadius: '8px',
                            background: 'rgba(0,0,0,0.1)'
                          }}
                        >
                          {videoResult.detections && videoResult.detections.filter(d => {
                            const matchesSearch = eventSearch === '' || 
                              (d.track_id !== null && d.track_id.toString().includes(eventSearch)) ||
                              (d.severity && d.severity.toLowerCase().includes(eventSearch.toLowerCase())) ||
                              (d.width_cm && d.width_cm.toString().includes(eventSearch));
                            const matchesSeverity = eventSeverityFilter[d.severity];
                            return matchesSearch && matchesSeverity;
                          }).length === 0 ? (
                            <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '12px' }}>
                              No Event Logs Match Filters.
                            </div>
                          ) : (
                            <table className="fintech-table" style={{ fontSize: '11px' }}>
                              <thead>
                                <tr>
                                  <th>FRAME</th>
                                  <th>TRACK ID</th>
                                  <th>SEVERITY</th>
                                  <th>WIDTH</th>
                                  <th>CONFIDENCE</th>
                                </tr>
                              </thead>
                              <tbody>
                                {videoResult.detections
                                  .filter(d => {
                                    const matchesSearch = eventSearch === '' || 
                                      (d.track_id !== null && d.track_id.toString().includes(eventSearch)) ||
                                      (d.severity && d.severity.toLowerCase().includes(eventSearch.toLowerCase())) ||
                                      (d.width_cm && d.width_cm.toString().includes(eventSearch));
                                    const matchesSeverity = eventSeverityFilter[d.severity];
                                    return matchesSearch && matchesSeverity;
                                  })
                                  .sort((a, b) => a.frame - b.frame)
                                  .map((det, dIdx) => {
                                    const maxFrame = videoResult.detections.reduce((max, d) => Math.max(max, d.frame), 0) || 1;
                                    const calculatedFPS = (videoDuration > 0 && maxFrame > 0) ? (maxFrame / videoDuration) : 25.0;
                                    const currentFrame = Math.round(videoTime * calculatedFPS);
                                    const isActive = Math.abs(det.frame - currentFrame) <= 5;
                                    
                                    return (
                                      <tr 
                                        key={dIdx}
                                        onClick={() => {
                                          if (processedVideoRef.current) {
                                            processedVideoRef.current.currentTime = det.frame / calculatedFPS;
                                          }
                                        }}
                                        className={isActive ? 'active-log-entry' : ''}
                                        style={{ 
                                          cursor: 'pointer',
                                          background: isActive ? 'rgba(6,182,212,0.06)' : 'transparent',
                                          transition: 'background 0.2s'
                                        }}
                                      >
                                        <td style={{ fontWeight: isActive ? '700' : '400', color: isActive ? 'var(--color-cyan)' : '#f1f5f9' }}>
                                          #{det.frame}
                                        </td>
                                        <td>{det.track_id !== null ? `Object #${det.track_id}` : 'Static'}</td>
                                        <td>
                                          <span className={`severity-pill ${det.severity === 'SEVERE' ? 'severity-pill-severe' : (det.severity === 'MODERATE' ? 'severity-pill-moderate' : 'severity-pill-minor')}`} style={{ padding: '2px 5px', fontSize: '9px' }}>
                                            <span className="severity-dot" />
                                            {det.severity}
                                          </span>
                                        </td>
                                        <td>{det.width_cm ? `${det.width_cm.toFixed(1)} cm` : 'N/A'}</td>
                                        <td className="mono-font">{(det.confidence * 100).toFixed(0)}%</td>
                                      </tr>
                                    );
                                  })}
                              </tbody>
                            </table>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Tab 2: Statistics content */}
                    {videoDetailTab === 'stats' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flexGrow: 1, overflowY: 'auto' }}>
                        {!videoResult.detections || videoResult.detections.length === 0 ? (
                          <div className="fallback-placeholder" style={{ padding: '40px' }}>No Data Available</div>
                        ) : (
                          <>
                            {/* Health overview */}
                            <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div>
                                <span style={{ fontSize: '10px', color: '#64748b', fontWeight: '600' }}>ROAD HEALTH INDEX</span>
                                <div style={{ fontSize: '20px', fontWeight: '700', color: videoResult.scan.road_health_score > 75 ? 'var(--color-minor)' : 'var(--color-moderate)' }}>
                                  Score: {videoResult.scan.road_health_score}%
                                </div>
                              </div>
                              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#94a3b8' }}>
                                <div>Minor: <b style={{ color: 'var(--color-minor)' }}>{videoResult.detections.filter(d => d.severity === 'MINOR').length}</b></div>
                                <div>Moderate: <b style={{ color: 'var(--color-moderate)' }}>{videoResult.detections.filter(d => d.severity === 'MODERATE').length}</b></div>
                                <div>Severe: <b style={{ color: 'var(--color-severe)' }}>{videoResult.detections.filter(d => d.severity === 'SEVERE').length}</b></div>
                              </div>
                            </div>

                            {/* Confidence Timeline Chart */}
                            <div className="glass-card">
                              <span style={{ fontSize: '10.5px', color: '#64748b', fontWeight: '700', display: 'block', marginBottom: '8px' }}>
                                CONFIDENCE LEVEL TIMELINE
                              </span>
                              <div style={{ width: '100%', height: '140px' }}>
                                <ResponsiveContainer>
                                  <AreaChart data={videoResult.detections.map(d => ({ frame: d.frame, confidence: Math.round(d.confidence * 100) })).sort((a,b) => a.frame - b.frame)}>
                                    <defs>
                                      <linearGradient id="colorScanConf" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--color-purple)" stopOpacity={0.2}/>
                                        <stop offset="95%" stopColor="var(--color-purple)" stopOpacity={0}/>
                                      </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.03)'} vertical={false} />
                                    <XAxis dataKey="frame" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                                    <YAxis stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                                    <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '10px', color: 'var(--text-primary)' }} />
                                    <Area type="monotone" dataKey="confidence" name="Confidence %" stroke="var(--color-purple)" fillOpacity={1} fill="url(#colorScanConf)" strokeWidth={1.5} />
                                  </AreaChart>
                                </ResponsiveContainer>
                              </div>
                            </div>

                            {/* Width Specs Distribution */}
                            <div className="glass-card">
                              <span style={{ fontSize: '10.5px', color: '#64748b', fontWeight: '700', display: 'block', marginBottom: '8px' }}>
                                POTHOLE WIDTH SPECS DISTRIBUTION
                              </span>
                              <div style={{ width: '100%', height: '140px' }}>
                                <ResponsiveContainer>
                                  <BarChart data={(() => {
                                    const localBuckets = { '<20cm': 0, '20-40cm': 0, '40-60cm': 0, '60-80cm': 0, '>80cm': 0 };
                                    videoResult.detections.forEach(d => {
                                      const w = d.width_cm || 0;
                                      if (w < 20) localBuckets['<20cm']++;
                                      else if (w < 40) localBuckets['20-40cm']++;
                                      else if (w < 60) localBuckets['40-60cm']++;
                                      else if (w < 80) localBuckets['60-80cm']++;
                                      else localBuckets['>80cm']++;
                                    });
                                    return Object.keys(localBuckets).map(key => ({ range: key, count: localBuckets[key] }));
                                  })()}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.03)'} vertical={false} />
                                    <XAxis dataKey="range" stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                                    <YAxis stroke={theme === 'ivory' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.2)'} fontSize={9} tickLine={false} />
                                    <Tooltip contentStyle={{ background: theme === 'ivory' ? '#fdfaf2' : '#0d1321', borderColor: 'var(--border-color)', borderRadius: '8px', fontSize: '10px', color: 'var(--text-primary)' }} />
                                    <Bar dataKey="count" fill="var(--color-cyan)" radius={[3, 3, 0, 0]} />
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    )}

                    {/* Tab 3: Exported Reports content */}
                    {videoDetailTab === 'reports' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1, overflowY: 'auto' }}>
                        <h4 style={{ fontSize: '12px', fontWeight: '600' }}>TELEMETRY DOWNLOAD DATA PACKS</h4>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                          <a
                            href={`${API_BASE}/api/download/${videoResult.scan._id}`}
                            className="fintech-btn"
                            style={{ textDecoration: 'none', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px', fontSize: '11px', padding: '10px' }}
                          >
                            <FileSpreadsheet size={13} /> Complete ZIP Payload
                          </a>
                          <button
                            onClick={() => {
                              const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(videoResult, null, 2));
                              const downloadAnchor = document.createElement('a');
                              downloadAnchor.setAttribute("href",     dataStr);
                              downloadAnchor.setAttribute("download", `telemetry_payload_${videoResult.scan._id}.json`);
                              document.body.appendChild(downloadAnchor);
                              downloadAnchor.click();
                              downloadAnchor.remove();
                            }}
                            className="fintech-btn fintech-btn-secondary"
                            style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px', fontSize: '11px', padding: '10px' }}
                          >
                            <Database size={13} /> Telemetry JSON Pack
                          </button>
                        </div>

                        <div style={{ marginTop: '16px' }}>
                          <span style={{ fontSize: '10px', color: '#64748b', fontWeight: '700', display: 'block', marginBottom: '8px' }}>
                            RAW TELEMETRY PAYLOAD VIEW
                          </span>
                          <pre style={{ 
                            background: 'rgba(0,0,0,0.3)', 
                            padding: '12px', 
                            borderRadius: '8px', 
                            fontSize: '9.5px', 
                            overflowX: 'auto', 
                            maxHeight: '180px',
                            border: '1px solid var(--border-color)',
                            color: 'rgba(255,255,255,0.7)',
                            fontFamily: 'JetBrains Mono'
                          }}>
                            {JSON.stringify(videoResult, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── LIVE WEBCAM TAB ─── */}
        {activeTab === 'webcam' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="glass-panel" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: '600' }}>Live Computer Vision Feed</h3>
                <p style={{ fontSize: '11px', color: '#64748b' }}>Uploading frame batches every 450ms to the core detection pipeline</p>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                {webcamActive ? (
                  <button 
                    onClick={stopWebcam}
                    className="fintech-btn"
                    style={{ background: 'rgba(239,68,68,0.1)', borderColor: 'var(--color-severe)', color: 'var(--color-severe)' }}
                  >
                    Disconnect Camera Stream
                  </button>
                ) : (
                  <button 
                    onClick={startWebcam}
                    className="fintech-btn"
                    style={{ background: 'rgba(16,185,129,0.1)', borderColor: 'var(--color-minor)', color: 'var(--color-minor)' }}
                  >
                    Connect Webcam Stream
                  </button>
                )}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '16px' }}>
              {/* Camera view container */}
              <div className="glass-panel" style={{ padding: '10px', display: 'flex', justifyContent: 'center', background: '#000', position: 'relative', borderRadius: '12px', overflow: 'hidden', minHeight: '340px' }}>
                <video 
                  ref={videoRef} 
                  style={{ display: 'none' }} 
                  width="640" 
                  height="480" 
                />
                
                {/* Canvas overlays */}
                <canvas 
                  ref={canvasRef} 
                  width="640" 
                  height="480" 
                  style={{ width: '100%', maxWidth: '640px', borderRadius: '8px', transform: 'scaleX(1)' }} 
                />
                
                {/* Live Warnings overlay */}
                {livePotholes.length > 0 && (
                  <div style={{
                    position: 'absolute', bottom: '16px', left: '16px', right: '16px',
                    background: liveCondition.color === 'var(--color-severe)' ? 'rgba(239,68,68,0.85)' : 'rgba(245,158,11,0.85)',
                    color: 'var(--text-header)', padding: '10px 14px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px',
                    boxShadow: '0 8px 16px rgba(0,0,0,0.3)', backdropFilter: 'blur(4px)', zIndex: 6
                  }}>
                    <AlertTriangle className="pulse-glow" size={16} />
                    <b style={{ fontSize: '12px' }}>{liveCondition.alert}</b>
                  </div>
                )}
              </div>

              {/* Live counts & GPS coords */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="glass-panel" style={{ padding: '16px', flexGrow: 1 }}>
                  <h3 style={{ fontSize: '12.5px', fontWeight: '600', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '6px' }}>
                    Live Detections Summary
                  </h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12.5px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#64748b' }}>Latitude:</span>
                      <b style={{ color: 'var(--text-header)', fontFamily: 'JetBrains Mono' }}>{currentGPS.current.lat.toFixed(6)}</b>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#64748b' }}>Longitude:</span>
                      <b style={{ color: 'var(--text-header)', fontFamily: 'JetBrains Mono' }}>{currentGPS.current.lon.toFixed(6)}</b>
                    </div>
                    <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: '4px 0' }} />
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#64748b' }}>Severe Potholes:</span>
                      <b style={{ color: 'var(--color-severe)', fontFamily: 'JetBrains Mono' }}>{livePotholes.filter(d => d.severity === 'SEVERE').length}</b>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#64748b' }}>Moderate Potholes:</span>
                      <b style={{ color: 'var(--color-moderate)', fontFamily: 'JetBrains Mono' }}>{livePotholes.filter(d => d.severity === 'MODERATE').length}</b>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#64748b' }}>Minor Potholes:</span>
                      <b style={{ color: 'var(--color-minor)', fontFamily: 'JetBrains Mono' }}>{livePotholes.filter(d => d.severity === 'MINOR').length}</b>
                    </div>
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '16px' }}>
                  <h4 style={{ fontSize: '12.5px', fontWeight: '600', marginBottom: '8px' }}>Geo-Uplink System</h4>
                  <div style={{ background: 'rgba(255,255,255,0.01)', padding: '12px', borderRadius: '8px', fontSize: '11.5px', border: '1px solid var(--border-color)' }}>
                    <MapPin style={{ color: 'var(--color-cyan)', marginBottom: '6px', display: 'block' }} size={16} />
                    <div style={{ color: '#64748b' }}>Detections are automatically timestamped and geolocated. Verified reports sync to the database coordinates pool.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ─── SCAN RECORDS HISTORY TAB ─── */}
        {activeTab === 'history' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: '600' }}>TELEMETRY SESSIONS ARCHIVE</h3>
                <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'JetBrains Mono' }}>Total Runs: {scans.length}</span>
              </div>

              {loadingHistory ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}><Loader2 className="pulse-glow" style={{ color: 'var(--color-cyan)' }} size={20} /></div>
              ) : (
                <table className="fintech-table">
                  <thead>
                    <tr>
                      <th>SCAN FILENAME</th>
                      <th>DATE CREATED</th>
                      <th>RUN TYPE</th>
                      <th>ANOMALIES</th>
                      <th>SAFETY PROFILE</th>
                      <th style={{ textAlign: 'center' }}>ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>No telemetry logs found in current node.</td>
                      </tr>
                    ) : (
                      scans.map((scan, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: '500', color: 'var(--text-header)' }}>{scan.scan_name}</td>
                          <td className="mono-font" style={{ fontSize: '12px' }}>{scan.date ? scan.date.replace('T', ' ').slice(0, 16) : 'N/A'}</td>
                          <td>
                            <span style={{
                              background: scan.scan_type === 'video' ? 'rgba(6,182,212,0.06)' : 'rgba(139,92,246,0.06)',
                              color: scan.scan_type === 'video' ? 'var(--color-cyan)' : 'var(--color-purple)',
                              border: `1px solid ${scan.scan_type === 'video' ? 'rgba(6,182,212,0.15)' : 'rgba(139,92,246,0.15)'}`,
                              padding: '2px 8px', borderRadius: '4px', fontSize: '10px', textTransform: 'uppercase', fontWeight: '700'
                            }}>
                              {scan.scan_type}
                            </span>
                          </td>
                          <td className="mono-font">{scan.total_potholes}</td>
                          <td style={{ fontWeight: '700', color: scan.road_health_score > 75 ? 'var(--color-minor)' : (scan.road_health_score > 50 ? 'var(--color-moderate)' : 'var(--color-severe)') }}>
                            {scan.road_health_score}%
                          </td>
                          <td style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                            <button 
                              onClick={() => showScanDetails(scan._id)}
                              className="fintech-btn fintech-btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11.5px', borderRadius: '6px' }}
                            >
                              Details
                            </button>
                            <button 
                              onClick={() => handleRerunScan(scan._id, scan.scan_type)}
                              className="fintech-btn"
                              title="Rerun Telemetry Scan"
                              style={{ background: 'rgba(6,182,212,0.1)', borderColor: 'rgba(6,182,212,0.2)', color: 'var(--color-cyan)', padding: '4px 8px', borderRadius: '6px' }}
                            >
                              <RefreshCw size={12} />
                            </button>
                            <a 
                              href={`${API_BASE}/api/download/${scan._id}`}
                              className="fintech-btn"
                              style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '11px' }}
                            >
                              <Download size={12} />
                            </a>
                            <button 
                              onClick={() => handleDeleteScan(scan._id)}
                              className="fintech-btn"
                              style={{ background: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.2)', color: 'var(--color-severe)', padding: '4px 8px', borderRadius: '6px' }}
                            >
                              <Trash2 size={12} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </div>

            {/* Scan Detailed Modal / View */}
            {activeScanDetail && (
              <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                  <h3 style={{ fontSize: '13.5px', fontWeight: '600' }}>RUN SPEC DETAILS: {activeScanDetail.scan.scan_name}</h3>
                  <button 
                    onClick={() => setActiveScanDetail(null)}
                    style={{ background: 'transparent', border: 0, color: '#64748b', cursor: 'pointer', fontSize: '12px', fontWeight: '500' }}
                  >
                    CLOSE DETAILS
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: '16px' }}>
                  {/* Media View */}
                  <div style={{ borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border-color)', position: 'relative' }}>
                    {activeScanDetail.scan.scan_type === 'video' ? (
                      <video 
                        key={activeScanDetail.scan.output_video_url}
                        controls 
                        src={`${API_BASE}${activeScanDetail.scan.output_video_url}`} 
                        style={{ width: '100%', display: 'block', borderRadius: '10px' }} 
                      />
                    ) : (
                      <>
                        <div className="optical-scan-bar" />
                        <img 
                          src={`${API_BASE}${activeScanDetail.scan.output_url}`} 
                          alt="Detections" 
                          style={{ width: '100%', display: 'block', borderRadius: '10px' }} 
                        />
                      </>
                    )}
                  </div>

                  {/* Telemetry metrics list */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                      <div className="glass-card" style={{ padding: '8px 12px', textAlign: 'center' }}>
                        <span style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', fontWeight: '600' }}>MINOR RUNS</span>
                        <div className="mono-font" style={{ fontSize: '16px', fontWeight: '700', color: 'var(--color-minor)' }}>{activeScanDetail.scan.minor}</div>
                      </div>
                      <div className="glass-card" style={{ padding: '8px 12px', textAlign: 'center' }}>
                        <span style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', fontWeight: '600' }}>MODERATE RUNS</span>
                        <div className="mono-font" style={{ fontSize: '16px', fontWeight: '700', color: 'var(--color-moderate)' }}>{activeScanDetail.scan.moderate}</div>
                      </div>
                      <div className="glass-card" style={{ padding: '8px 12px', textAlign: 'center' }}>
                        <span style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', fontWeight: '600' }}>SEVERE RUNS</span>
                        <div className="mono-font" style={{ fontSize: '16px', fontWeight: '700', color: 'var(--color-severe)' }}>{activeScanDetail.scan.severe}</div>
                      </div>
                    </div>

                    <div className="glass-card" style={{ overflowY: 'auto', maxHeight: '180px' }}>
                      <h4 style={{ fontSize: '11.5px', color: 'var(--text-header)', marginBottom: '6px', fontWeight: '600' }}>Detections Telemetry ({activeScanDetail.detections.length})</h4>
                      <table className="fintech-table" style={{ fontSize: '11px' }}>
                        <thead>
                          <tr>
                            <th>TRACK OBJECT</th>
                            <th>SEVERITY</th>
                            <th>EST WIDTH</th>
                            <th>DISTANCE</th>
                            <th>COORDINATES</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activeScanDetail.detections.map((det, dIdx) => (
                            <tr key={dIdx}>
                              <td>{det.track_id !== null ? `#${det.track_id}` : 'Static'}</td>
                              <td>
                                <span className={`severity-pill ${det.severity === 'SEVERE' ? 'severity-pill-severe' : (det.severity === 'MODERATE' ? 'severity-pill-moderate' : 'severity-pill-minor')}`} style={{ padding: '2px 5px', fontSize: '9px' }}>
                                  <span className="severity-dot" />
                                  {det.severity}
                                </span>
                              </td>
                              <td>{det.width_cm ? `${det.width_cm.toFixed(1)} cm` : 'N/A'}</td>
                              <td>{det.distance_m ? `${det.distance_m.toFixed(1)} m` : 'N/A'}</td>
                              <td className="mono-font" style={{ fontSize: '10px' }}>{det.lat ? `${det.lat.toFixed(4)}, ${det.lon.toFixed(4)}` : 'N/A'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
