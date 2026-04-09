// src/components/LandingPage.jsx

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);

// ============================================
// SPLIT WORDS — per-word reveal animation
// ============================================
const SplitWords = ({ children, className = '' }) => {
    const text = typeof children === 'string' ? children : '';
    return (
        <span className={`split-words ${className}`}>
            {text.split(' ').map((word, i) => (
                <span className="word-wrap" key={i}>
                    <span className="word">{word}</span>
                </span>
            ))}
        </span>
    );
};

// ============================================
// MAGNETIC BUTTON — cursor-following wrapper
// ============================================
const MagneticButton = ({ children, className = '' }) => {
    const ref = useRef(null);
    useEffect(() => {
        const el = ref.current;
        if (!el || window.matchMedia('(hover: none)').matches) return;
        const onMove = (e) => {
            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            gsap.to(el, { x: x * 0.3, y: y * 0.3, duration: 0.4, ease: 'power3.out' });
        };
        const onLeave = () => {
            gsap.to(el, { x: 0, y: 0, duration: 0.7, ease: 'elastic.out(1, 0.3)' });
        };
        el.addEventListener('mousemove', onMove);
        el.addEventListener('mouseleave', onLeave);
        return () => { el.removeEventListener('mousemove', onMove); el.removeEventListener('mouseleave', onLeave); };
    }, []);
    return <div ref={ref} className={`magnetic-wrap ${className}`} style={{ display: 'inline-block' }}>{children}</div>;
};

// ============================================
// FLOATING ELEMENTS — parallax circles
// ============================================
const FloatingElements = ({ section = 'hero' }) => (
    <div className={`floating-elements floating-${section}`} aria-hidden="true">
        <div className="float-circle float-circle-1" data-speed="0.5" />
        <div className="float-circle float-circle-2" data-speed="-0.3" />
        <div className="float-circle float-circle-3" data-speed="0.7" />
    </div>
);

// ============================================
// COMPARISON SECTION
// ============================================
const oldWayItems = [
    { label: 'Research agencies & freelancers', value: 'Weeks of searching' },
    { label: '4–8 weeks delivery time', value: '4–8 wks' },
    { label: 'Complex technical setup', value: 'Dev needed' },
    { label: 'Endless revision rounds', value: '10+ rounds' },
    { label: 'Separate hosting setup', value: 'Extra fees' },
];

const newWayItems = [
    { label: 'One prompt, done', value: '1 prompt' },
    { label: '60 seconds delivery', value: '60s', counter: 60, suffix: 's' },
    { label: 'No coding required', value: 'Zero code' },
    { label: 'Edit anything instantly', value: 'Instant' },
    { label: 'One-click deploy with SSL', value: '1 click' },
];

const ComparisonSection = () => {
    const ref = useRef(null);
    const [activeCard, setActiveCard] = useState('both'); // 'old', 'new', 'both'
    const [hoveredItem, setHoveredItem] = useState(null);
    const itemRefs = useRef([]); // eslint-disable-line no-unused-vars

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Heading entrance
            gsap.fromTo('.comparison-heading > *', { y: 40, opacity: 0 }, {
                y: 0, opacity: 1, stagger: 0.1, duration: 0.8, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 80%' }
            });

            // Toggle pills entrance
            gsap.fromTo('.comparison-toggle', { y: 20, opacity: 0 }, {
                y: 0, opacity: 1, duration: 0.6, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 78%' }
            });

            // Cards slide in from opposite sides
            gsap.fromTo('.comparison-old', { x: -100, opacity: 0 }, {
                x: 0, opacity: 1, duration: 1, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 75%' }
            });
            gsap.fromTo('.comparison-new', { x: 100, opacity: 0 }, {
                x: 0, opacity: 1, duration: 1, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 75%' }
            });

            // VS badge bounce in
            gsap.fromTo('.comparison-vs', { scale: 0, opacity: 0, rotation: -180 }, {
                scale: 1, opacity: 1, rotation: 0, duration: 0.8, ease: 'back.out(2)',
                scrollTrigger: { trigger: ref.current, start: 'top 70%' }
            });

            // Staggered item reveal — old side
            gsap.fromTo('.comparison-old .comparison-item', { x: -30, opacity: 0 }, {
                x: 0, opacity: 1, stagger: 0.12, duration: 0.5, ease: 'power2.out',
                scrollTrigger: { trigger: ref.current, start: 'top 68%' }
            });

            // Staggered item reveal — new side
            gsap.fromTo('.comparison-new .comparison-item', { x: 30, opacity: 0 }, {
                x: 0, opacity: 1, stagger: 0.12, duration: 0.5, ease: 'power2.out',
                scrollTrigger: { trigger: ref.current, start: 'top 68%' }
            });

            // Bottom stats bar
            gsap.fromTo('.comparison-stats', { y: 30, opacity: 0 }, {
                y: 0, opacity: 1, duration: 0.8, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 55%' }
            });
        }, ref);
        return () => ctx.revert();
    }, []);

    // Animated hover on list items — subtle scale + glow
    const handleItemEnter = (key) => setHoveredItem(key);
    const handleItemLeave = () => setHoveredItem(null);

    return (
        <section className="comparison-section" ref={ref}>
            <div className="comparison-inner">
                <div className="comparison-heading">
                    <span className="section-tag">Why Web AI</span>
                    <h2>The <span className="text-accent">Smarter</span> Way to Build</h2>
                    <p className="comparison-subtitle">See how Web AI eliminates the complexity of traditional web development</p>
                </div>

                {/* Toggle pills for mobile focus */}
                <div className="comparison-toggle">
                    {['both','old','new'].map(v => (
                        <button
                            key={v}
                            className={`comparison-toggle-btn ${activeCard === v ? 'active' : ''}`}
                            onClick={() => setActiveCard(v)}
                        >
                            {v === 'both' ? 'Compare' : v === 'old' ? 'Old Way' : 'Web AI Way'}
                        </button>
                    ))}
                </div>

                <div className="comparison-cards">
                    <div className={`comparison-card comparison-old glow-card${activeCard === 'new' ? ' comparison-card-dimmed' : ''}${activeCard === 'old' ? ' comparison-card-focused' : ''}`}>
                        <div className="comparison-card-header">
                            <span className="comparison-icon comparison-icon-old">✕</span>
                            <h3>The Old Way</h3>
                            <span className="comparison-badge comparison-badge-old">Outdated</span>
                        </div>
                        <ul className="comparison-list">
                            {oldWayItems.map((item, i) => (
                                <li
                                    key={i}
                                    className={`comparison-item strikethrough${hoveredItem === `old-${i}` ? ' comparison-item-hovered' : ''}`}
                                    onMouseEnter={() => handleItemEnter(`old-${i}`)}
                                    onMouseLeave={handleItemLeave}
                                >
                                    <span className="comp-label">{item.label}</span>
                                    <span className="comp-value comp-value-old">{item.value}</span>
                                </li>
                            ))}
                        </ul>
                        <div className="comparison-card-footer comparison-card-footer-old">
                            Slow, expensive, frustrating
                        </div>
                    </div>

                    <div className={`comparison-vs${activeCard !== 'both' ? ' comparison-vs-hidden' : ''}`}>
                        <span className="comparison-vs-text">VS</span>
                        <div className="comparison-vs-pulse"></div>
                    </div>

                    <div className={`comparison-card comparison-new glow-card${activeCard === 'old' ? ' comparison-card-dimmed' : ''}${activeCard === 'new' ? ' comparison-card-focused' : ''}`}>
                        <div className="comparison-card-header">
                            <span className="comparison-icon comparison-icon-new">✓</span>
                            <h3>The Web AI Way</h3>
                            <span className="comparison-badge comparison-badge-new">Recommended</span>
                        </div>
                        <ul className="comparison-list">
                            {newWayItems.map((item, i) => (
                                <li
                                    key={i}
                                    className={`comparison-item highlight${hoveredItem === `new-${i}` ? ' comparison-item-hovered' : ''}`}
                                    onMouseEnter={() => handleItemEnter(`new-${i}`)}
                                    onMouseLeave={handleItemLeave}
                                >
                                    <span className="comp-label">{item.label}</span>
                                    <span className="comp-value comp-value-new">{item.value}</span>
                                </li>
                            ))}
                        </ul>
                        <div className="comparison-card-footer comparison-card-footer-new">
                            Fast, free, effortless
                        </div>
                    </div>
                </div>

                {/* Bottom stats bar */}
                <div className="comparison-stats">
                    <div className="comparison-stat">
                        <span className="comparison-stat-number">100×</span>
                        <span className="comparison-stat-label">Faster</span>
                    </div>
                    <div className="comparison-stat-divider"></div>
                    <div className="comparison-stat">
                        <span className="comparison-stat-number">0 Code</span>
                        <span className="comparison-stat-label">Required</span>
                    </div>
                    <div className="comparison-stat-divider"></div>
                    <div className="comparison-stat">
                        <span className="comparison-stat-number">∞</span>
                        <span className="comparison-stat-label">Edits</span>
                    </div>
                    <div className="comparison-stat-divider"></div>
                    <div className="comparison-stat">
                        <span className="comparison-stat-number">1-Click</span>
                        <span className="comparison-stat-label">Deploy</span>
                    </div>
                </div>
            </div>
        </section>
    );
};

// ============================================
// TEMPLATE GALLERY — scroll-linked horizontal
// ============================================

// Each card has its own unique inline mockup via the `render` function
const templateData = [
    { name: 'Real Estate', category: 'Business',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#1a1a2e',fontFamily:'Inter,system-ui,sans-serif'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 14px',borderBottom:'1px solid rgba(201,164,92,0.15)'}}>
            <span style={{color:'#c9a45c',fontWeight:800,fontSize:11}}>Prestige<span style={{color:'#fff'}}>Realty</span></span>
            <div style={{display:'flex',gap:10,fontSize:7,color:'rgba(201,164,92,0.6)'}}>
              <span>Properties</span><span>About</span><span>Contact</span>
            </div>
          </div>
          <div style={{flex:1,background:'linear-gradient(135deg,#1a1a2e 40%,#2a2040)',display:'flex',alignItems:'center',padding:'0 14px',gap:12}}>
            <div style={{flex:1}}>
              <div style={{fontSize:6,letterSpacing:2,color:'#c9a45c',marginBottom:6,fontWeight:700}}>PREMIUM LISTINGS</div>
              <div style={{fontSize:16,fontWeight:800,color:'#fff',lineHeight:1.15,marginBottom:6}}>Find Your Dream<br/>Home in Dubai</div>
              <div style={{fontSize:7,color:'rgba(255,255,255,0.45)',marginBottom:10,lineHeight:1.5}}>Exclusive properties across Dubai's most prestigious neighborhoods.</div>
              <div style={{display:'inline-block',background:'#c9a45c',color:'#1a1a2e',padding:'4px 14px',borderRadius:4,fontSize:7,fontWeight:700}}>Browse Properties</div>
            </div>
            <div style={{width:100,height:80,borderRadius:8,background:'linear-gradient(135deg,#2d2d5e,#c9a45c33)',display:'flex',alignItems:'flex-end',padding:6}}>
              <div style={{background:'rgba(0,0,0,0.4)',borderRadius:4,padding:'3px 6px',fontSize:6,color:'#fff',fontWeight:600}}>AED 4.5M</div>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',background:'#1a1a2e'}}>
            {['Marina Penthouse·AED 2.8M','Creek Harbour·AED 1.6M','JBR Villa·AED 5.2M'].map((c,i)=>(
              <div key={i} style={{flex:1,background:'rgba(201,164,92,0.06)',border:'1px solid rgba(201,164,92,0.12)',borderRadius:5,padding:'4px 6px'}}>
                <div style={{height:18,background:'linear-gradient(135deg,rgba(201,164,92,0.15),rgba(201,164,92,0.05))',borderRadius:3,marginBottom:3}}/>
                <div style={{fontSize:6,color:'#fff',fontWeight:600}}>{c.split('·')[0]}</div>
                <div style={{fontSize:6,color:'#c9a45c'}}>{c.split('·')[1]}</div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Restaurant', category: 'Food & Drink',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#0f0f0f',fontFamily:'Georgia,serif'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'10px 14px',borderBottom:'1px solid #222'}}>
            <span style={{color:'#e8d5b5',fontSize:11,letterSpacing:3,fontWeight:400}}>SAFFRON</span>
            <div style={{display:'flex',gap:10,fontSize:7,letterSpacing:1,color:'#666'}}>
              <span>MENU</span><span>STORY</span>
              <span style={{background:'#c9a45c',color:'#0f0f0f',padding:'2px 8px',borderRadius:2,fontWeight:700,fontFamily:'system-ui'}}>Reserve</span>
            </div>
          </div>
          <div style={{flex:1,background:'linear-gradient(180deg,#1a1512 0%,#0f0f0f 100%)',textAlign:'center',display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',padding:'12px 14px'}}>
            <div style={{fontSize:6,letterSpacing:4,color:'#c9a45c',marginBottom:8}}>FINE DINING EXPERIENCE</div>
            <div style={{fontSize:18,color:'#fff',fontWeight:400,lineHeight:1.2,marginBottom:6}}>Where Culinary Art<br/>Meets Elegance</div>
            <div style={{fontSize:7,color:'#888',fontStyle:'italic',marginBottom:10,maxWidth:200,lineHeight:1.5}}>An exquisite journey through Middle Eastern flavors, reimagined with modern French techniques.</div>
            <div style={{display:'flex',gap:6}}>
              <span style={{background:'#c9a45c',color:'#0f0f0f',padding:'4px 14px',borderRadius:2,fontSize:7,fontWeight:700,fontFamily:'system-ui'}}>Book a Table</span>
              <span style={{border:'1px solid rgba(255,255,255,0.2)',padding:'4px 14px',borderRadius:2,fontSize:7,color:'#aaa',fontFamily:'system-ui'}}>View Menu</span>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',background:'#0a0a0a'}}>
            {['Saffron Lamb·AED 185','Truffle Hummus·AED 95','Pistachio Kunafa·AED 65'].map((c,i)=>(
              <div key={i} style={{flex:1,background:'#1a1a1a',border:'1px solid #222',borderRadius:6,overflow:'hidden'}}>
                <div style={{height:20,background:`linear-gradient(135deg,#c9a45c11,#c9a45c06)`}}/>
                <div style={{padding:'4px 6px'}}><div style={{fontSize:6,color:'#fff'}}>{c.split('·')[0]}</div><div style={{fontSize:6,color:'#c9a45c',fontFamily:'system-ui',fontWeight:700}}>{c.split('·')[1]}</div></div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Fitness Studio', category: 'Health',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#111',fontFamily:'system-ui,sans-serif',color:'#fff'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 14px'}}>
            <span style={{fontSize:12,fontWeight:900,letterSpacing:-0.5}}>APEX<span style={{color:'#ff4d4d'}}>FIT</span></span>
            <div style={{display:'flex',gap:10,fontSize:7,fontWeight:600,color:'#666',alignItems:'center'}}>
              <span>Classes</span><span>Trainers</span>
              <span style={{background:'#ff4d4d',color:'#fff',padding:'2px 8px',borderRadius:4,fontWeight:700}}>Join</span>
            </div>
          </div>
          <div style={{flex:1,display:'flex',padding:'8px 14px',gap:10,alignItems:'center'}}>
            <div style={{flex:1}}>
              <div style={{display:'inline-block',background:'rgba(255,77,77,0.12)',color:'#ff4d4d',fontSize:6,fontWeight:800,padding:'2px 8px',borderRadius:10,letterSpacing:1,marginBottom:6}}>NO EXCUSES</div>
              <div style={{fontSize:16,fontWeight:900,lineHeight:1.1,marginBottom:6}}>Transform Your<br/>Body & Mind</div>
              <div style={{fontSize:7,color:'#777',marginBottom:8,lineHeight:1.6}}>Dubai's premier fitness studio. Expert trainers, 50+ weekly classes.</div>
              <div style={{display:'inline-block',background:'#ff4d4d',color:'#fff',padding:'4px 14px',borderRadius:6,fontSize:7,fontWeight:700}}>Start Free Trial</div>
              <div style={{display:'flex',gap:14,marginTop:10}}>
                {[['50+','Classes'],['15','Trainers'],['2K+','Members']].map(([n,l],i)=>(
                  <div key={i}><div style={{fontSize:12,fontWeight:900,color:i===0?'#ff4d4d':'#fff'}}>{n}</div><div style={{fontSize:5,color:'#666'}}>{l}</div></div>
                ))}
              </div>
            </div>
            <div style={{width:90,height:100,borderRadius:10,background:'linear-gradient(135deg,#222,#ff4d4d15)',display:'flex',alignItems:'center',justifyContent:'center'}}>
              <div style={{fontSize:24,fontWeight:900,opacity:0.15}}>APEX</div>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'6px 14px 10px',background:'#0a0a0a'}}>
            {['Boxing·Mon/Wed/Fri','Power Yoga·Daily 6AM','CrossFit·Tue/Thu'].map((c,i)=>(
              <div key={i} style={{flex:1,background:'#1a1a1a',border:'1px solid #222',borderRadius:6,overflow:'hidden'}}>
                <div style={{height:16,background:'linear-gradient(135deg,#ff4d4d10,#ff4d4d05)'}}/>
                <div style={{padding:'3px 6px'}}><div style={{fontSize:6,fontWeight:700}}>{c.split('·')[0]}</div><div style={{fontSize:5,color:'#ff4d4d',fontWeight:700}}>{c.split('·')[1]}</div></div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Tech Startup', category: 'Technology',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#0a192f',fontFamily:'system-ui,sans-serif'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 14px',borderBottom:'1px solid #1a2d4a'}}>
            <span style={{color:'#64ffda',fontWeight:700,fontSize:11}}>Nova<span style={{color:'#ccd6f6'}}>Tech</span></span>
            <div style={{display:'flex',gap:10,fontSize:7,color:'#8892b0'}}>
              <span>Product</span><span>Pricing</span><span>Docs</span>
            </div>
          </div>
          <div style={{flex:1,display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',textAlign:'center',padding:14}}>
            <div style={{display:'inline-block',border:'1px solid #64ffda40',padding:'2px 10px',borderRadius:20,fontSize:6,color:'#64ffda',fontWeight:600,letterSpacing:1,marginBottom:8}}>AI-POWERED PLATFORM</div>
            <div style={{fontSize:18,fontWeight:800,color:'#ccd6f6',lineHeight:1.15,marginBottom:6}}>Build the Future<br/><span style={{color:'#64ffda'}}>of Automation</span></div>
            <div style={{fontSize:7,color:'#8892b0',marginBottom:10,lineHeight:1.6,maxWidth:200}}>Ship faster with intelligent workflows. From idea to production in minutes.</div>
            <div style={{display:'flex',gap:6}}>
              <span style={{background:'#64ffda',color:'#0a192f',padding:'4px 14px',borderRadius:6,fontSize:7,fontWeight:700}}>Get Started Free</span>
              <span style={{border:'1px solid #64ffda40',padding:'4px 14px',borderRadius:6,fontSize:7,color:'#64ffda'}}>Live Demo</span>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',background:'#071221'}}>
            {[['Analytics','Real-time dashboards'],['Automation','Smart workflows'],['Security','Enterprise-grade']].map(([t,s],i)=>(
              <div key={i} style={{flex:1,background:'#0a192f',border:'1px solid #1a2d4a',borderRadius:6,padding:'6px 8px'}}>
                <div style={{fontSize:7,color:'#ccd6f6',fontWeight:700,marginBottom:2}}>{t}</div>
                <div style={{fontSize:5,color:'#64ffda99'}}>{s}</div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Fashion Brand', category: 'Retail',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#faf8f5',fontFamily:'Georgia,serif',color:'#1a1a1a'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'10px 14px',borderBottom:'1px solid #e8e4de'}}>
            <span style={{fontSize:12,letterSpacing:4,fontWeight:400,color:'#1a1a1a'}}>MAISON</span>
            <div style={{display:'flex',gap:10,fontSize:7,letterSpacing:0.5,color:'#888'}}>
              <span>Collection</span><span>Lookbook</span><span>Stores</span>
            </div>
          </div>
          <div style={{flex:1,display:'flex',alignItems:'center',padding:'0 14px',gap:10,background:'linear-gradient(180deg,#faf8f5,#f3ede5)'}}>
            <div style={{flex:1}}>
              <div style={{fontSize:6,letterSpacing:3,color:'#a08060',marginBottom:6,fontWeight:600,fontFamily:'system-ui'}}>NEW SEASON '26</div>
              <div style={{fontSize:18,fontWeight:400,lineHeight:1.2,marginBottom:6,color:'#1a1a1a'}}>Timeless<br/>Elegance</div>
              <div style={{fontSize:7,color:'#999',marginBottom:10,lineHeight:1.6,fontFamily:'system-ui'}}>Curated pieces for the modern wardrobe. Crafted with intention.</div>
              <div style={{display:'inline-block',background:'#1a1a1a',color:'#faf8f5',padding:'4px 16px',borderRadius:2,fontSize:7,fontWeight:600,fontFamily:'system-ui'}}>Shop Now</div>
            </div>
            <div style={{width:90,height:110,borderRadius:4,background:'linear-gradient(180deg,#e8ddd0,#d4c4b0)',display:'flex',alignItems:'center',justifyContent:'center'}}>
              <div style={{fontSize:20,color:'#1a1a1a',opacity:0.1,fontWeight:400,letterSpacing:4}}>M</div>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',background:'#faf8f5',borderTop:'1px solid #e8e4de'}}>
            {['Essentials·From AED 450','Evening Wear·From AED 1,200','Accessories·From AED 280'].map((c,i)=>(
              <div key={i} style={{flex:1,border:'1px solid #e8e4de',borderRadius:4,overflow:'hidden'}}>
                <div style={{height:20,background:i===0?'#e8ddd0':i===1?'#1a1a1a':'#d4c4b0'}}/>
                <div style={{padding:'4px 6px'}}><div style={{fontSize:6,fontWeight:600,fontFamily:'system-ui'}}>{c.split('·')[0]}</div><div style={{fontSize:5,color:'#a08060',fontFamily:'system-ui'}}>{c.split('·')[1]}</div></div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Law Firm', category: 'Professional',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#f7f5f2',fontFamily:'Georgia,serif',color:'#1b2838'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'10px 14px',background:'#1b2838'}}>
            <span style={{color:'#d4c4a8',fontSize:10,fontWeight:400,letterSpacing:1}}>AL RASHID <span style={{fontWeight:700}}>LEGAL</span></span>
            <div style={{display:'flex',gap:10,fontSize:7,color:'rgba(255,255,255,0.5)'}}>
              <span>Practice</span><span>Team</span><span>Contact</span>
            </div>
          </div>
          <div style={{flex:1,background:'linear-gradient(180deg,#1b2838 0%,#2a3a4e 100%)',display:'flex',flexDirection:'column',justifyContent:'center',padding:'0 14px'}}>
            <div style={{width:24,height:2,background:'#8b7355',marginBottom:10}}/>
            <div style={{fontSize:6,color:'#8b7355',letterSpacing:2,fontWeight:600,marginBottom:6,fontFamily:'system-ui'}}>ESTABLISHED 1998</div>
            <div style={{fontSize:18,color:'#fff',fontWeight:400,lineHeight:1.2,marginBottom:8}}>Trusted Legal<br/>Counsel in Dubai</div>
            <div style={{fontSize:7,color:'rgba(255,255,255,0.45)',marginBottom:10,lineHeight:1.6,fontFamily:'system-ui'}}>Over 25 years of excellence in corporate, real estate, and litigation law.</div>
            <div style={{display:'inline-block',border:'1px solid #8b7355',color:'#8b7355',padding:'4px 14px',borderRadius:2,fontSize:7,fontWeight:600,fontFamily:'system-ui',width:'fit-content'}}>Book Consultation</div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',background:'#f7f5f2',borderTop:'1px solid #e8e2d8'}}>
            {['Corporate Law','Real Estate','Litigation'].map((t,i)=>(
              <div key={i} style={{flex:1,background:'#fff',border:'1px solid #e8e2d8',borderRadius:4,padding:'6px 8px'}}>
                <div style={{fontSize:7,color:'#1b2838',fontWeight:700,fontFamily:'system-ui'}}>{t}</div>
                <div style={{fontSize:5,color:'#8b7355',fontFamily:'system-ui',marginTop:2}}>Learn more →</div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Travel Agency', category: 'Travel',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#003049',fontFamily:'system-ui,sans-serif'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 14px',borderBottom:'1px solid #0a4060'}}>
            <span style={{color:'#f77f00',fontWeight:800,fontSize:11}}>Wanderlust</span>
            <div style={{display:'flex',gap:10,fontSize:7,color:'rgba(255,255,255,0.5)'}}>
              <span>Destinations</span><span>Deals</span><span>About</span>
            </div>
          </div>
          <div style={{flex:1,position:'relative',display:'flex',flexDirection:'column',justifyContent:'center',padding:'0 14px'}}>
            <div style={{position:'absolute',top:10,right:14,background:'#f77f00',color:'#003049',padding:'2px 8px',borderRadius:10,fontSize:6,fontWeight:800}}>30% OFF</div>
            <div style={{fontSize:6,letterSpacing:2,color:'#f77f00',fontWeight:700,marginBottom:6}}>CURATED JOURNEYS</div>
            <div style={{fontSize:18,fontWeight:800,color:'#fff',lineHeight:1.15,marginBottom:6}}>Explore the<br/>World with Us</div>
            <div style={{fontSize:7,color:'rgba(255,255,255,0.45)',marginBottom:10,lineHeight:1.5}}>Handpicked destinations. Unforgettable experiences. Expert-planned itineraries.</div>
            <div style={{display:'flex',gap:6}}>
              <span style={{background:'#f77f00',color:'#003049',padding:'4px 14px',borderRadius:6,fontSize:7,fontWeight:700}}>Plan Your Trip</span>
              <span style={{border:'1px solid #f77f0060',padding:'4px 14px',borderRadius:6,fontSize:7,color:'#f77f00'}}>View Deals</span>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',background:'#002438'}}>
            {[['Maldives','From $2,499'],['Santorini','From $1,899'],['Bali','From $1,599']].map(([t,s],i)=>(
              <div key={i} style={{flex:1,background:'#003049',border:'1px solid #0a4060',borderRadius:6,overflow:'hidden'}}>
                <div style={{height:22,background:`linear-gradient(135deg,#f77f0015,#f77f0005)`}}/>
                <div style={{padding:'4px 6px'}}><div style={{fontSize:7,color:'#fff',fontWeight:700}}>{t}</div><div style={{fontSize:6,color:'#f77f00'}}>{s}</div></div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    { name: 'Coffee Shop', category: 'Food & Drink',
      render: () => (
        <div style={{height:'100%',display:'flex',flexDirection:'column',background:'#faf6f1',fontFamily:'system-ui,sans-serif',color:'#2c1a0e'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 14px',borderBottom:'1px solid #e8ddd0'}}>
            <span style={{fontWeight:800,fontSize:10,color:'#2c1a0e'}}>Ember <span style={{color:'#d4a574'}}>&</span> Brew</span>
            <div style={{display:'flex',gap:10,fontSize:7,color:'#a08060'}}>
              <span>Menu</span><span>Story</span><span>Locations</span>
            </div>
          </div>
          <div style={{flex:1,display:'flex',alignItems:'center',gap:10,padding:'0 14px',background:'linear-gradient(135deg,#faf6f1,#f0e8dc)'}}>
            <div style={{flex:1}}>
              <div style={{fontSize:6,letterSpacing:2,color:'#d4a574',fontWeight:700,marginBottom:6}}>SINGLE ORIGIN</div>
              <div style={{fontSize:18,fontWeight:800,lineHeight:1.15,marginBottom:6}}>Craft Coffee<br/>Culture</div>
              <div style={{fontSize:7,color:'#8a7060',marginBottom:10,lineHeight:1.5}}>Ethically sourced, expertly roasted. Every cup tells a story.</div>
              <div style={{display:'inline-block',background:'#2c1a0e',color:'#faf6f1',padding:'4px 14px',borderRadius:20,fontSize:7,fontWeight:700}}>Order Online</div>
            </div>
            <div style={{width:80,height:80,borderRadius:'50%',background:'linear-gradient(135deg,#d4a574,#8a6040)',display:'flex',alignItems:'center',justifyContent:'center'}}>
              <div style={{width:50,height:50,borderRadius:'50%',background:'#2c1a0e',display:'flex',alignItems:'center',justifyContent:'center',fontSize:7,color:'#d4a574',fontWeight:800}}>E&B</div>
            </div>
          </div>
          <div style={{display:'flex',gap:6,padding:'8px 14px',borderTop:'1px solid #e8ddd0',background:'#faf6f1'}}>
            {[['Espresso','AED 18'],['Pour Over','AED 24'],['Cold Brew','AED 22']].map(([t,s],i)=>(
              <div key={i} style={{flex:1,background:'#fff',border:'1px solid #e8ddd0',borderRadius:8,padding:'6px 8px',textAlign:'center'}}>
                <div style={{fontSize:7,fontWeight:700}}>{t}</div>
                <div style={{fontSize:6,color:'#d4a574',fontWeight:600}}>{s}</div>
              </div>
            ))}
          </div>
        </div>
      ),
    },
];

const TemplateGallery = () => {
    const trackRef = useRef(null);

    // Pause animation on hover
    const handleMouseEnter = () => {
        if (trackRef.current) trackRef.current.style.animationPlayState = 'paused';
    };
    const handleMouseLeave = () => {
        if (trackRef.current) trackRef.current.style.animationPlayState = 'running';
    };

    // Render cards — duplicate the set for seamless loop
    const cards = [...templateData, ...templateData];

    return (
        <section className="gallery-section">
            <div className="gallery-heading">
                <span className="section-tag">Templates</span>
                <h2>Beautiful Templates, <span className="text-accent">Ready in Seconds</span></h2>
                <p>Every industry covered. Pick a direction or let AI surprise you.</p>
            </div>
            <div className="gallery-marquee">
                <div
                    className="gallery-track"
                    ref={trackRef}
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    {cards.map((t, i) => (
                        <div className="gallery-card glow-card" key={i}>
                            <div className="gallery-card-preview">
                                {t.render()}
                            </div>
                            <div className="gallery-card-info">
                                <span className="gallery-category">{t.category}</span>
                                <h4>{t.name}</h4>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

// ============================================
// FAQ SECTION
// ============================================
const faqData = [
    { q: 'How does the AI website generator work?', a: 'Simply describe your business and what you want in plain language. Our AI analyzes your prompt and generates a complete, professional website with relevant content, images, and styling — all in under 60 seconds.' },
    { q: 'Can I edit the generated website?', a: 'Absolutely. After generation, you can click any element to edit text, change colors, swap images, and modify layouts. You can also send follow-up prompts to make changes using natural language.' },
    { q: 'Do I need coding or design experience?', a: 'Not at all. The entire process is designed for non-technical users. If you can describe what you want in plain English, you can build a professional website.' },
    { q: 'How do I deploy my website?', a: 'Just click the "Deploy" button. Your website goes live instantly with a custom subdomain (yoursite.meydanfz.ae), free SSL certificate, and global CDN for fast loading worldwide.' },
    { q: 'Can I use my own domain name?', a: 'Yes. You can connect any custom domain to your generated website. We provide simple DNS instructions, and SSL is automatically provisioned for your domain.' },
    { q: 'What industries are supported?', a: 'Our AI handles all industries — real estate, restaurants, fitness, technology, fashion, legal, travel, healthcare, education, and many more. It adapts content and design to match your specific industry.' },
    { q: 'Is my website mobile-responsive?', a: 'Every generated website is fully responsive out of the box. It looks great on desktops, tablets, and smartphones without any extra configuration.' },
];

// AI Agent FAQ — gradient orb with cards that "speak" via typewriter answers.
// Replaces the legacy static accordion. Spec lives in
// memory/todo-ai-agent-faq.md. All classes are namespaced .aif-* so they
// can't collide with the legacy .faq-* CSS still used elsewhere.
const FAQSection = () => {
    const ref = useRef(null);
    const [openIndex, setOpenIndex] = useState(null);
    const [typed, setTyped] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const typingTimerRef = useRef(null);
    const startDelayRef = useRef(null);

    // Typewriter effect — runs every time the open card changes.
    // Pre-typing pause (450ms) simulates "thinking", then chars reveal at
    // 25ms each. Cancellable via cleanup so rapid card switches don't pile
    // up overlapping timers.
    useEffect(() => {
        if (typingTimerRef.current) { clearTimeout(typingTimerRef.current); typingTimerRef.current = null; }
        if (startDelayRef.current) { clearTimeout(startDelayRef.current); startDelayRef.current = null; }

        if (openIndex === null) {
            setTyped('');
            setIsTyping(false);
            return;
        }

        const fullAnswer = faqData[openIndex].a;
        setTyped('');
        setIsTyping(true);

        startDelayRef.current = setTimeout(() => {
            let i = 0;
            const tick = () => {
                if (i < fullAnswer.length) {
                    i += 1;
                    setTyped(fullAnswer.slice(0, i));
                    typingTimerRef.current = setTimeout(tick, 25);
                } else {
                    setIsTyping(false);
                }
            };
            tick();
        }, 450);

        return () => {
            if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
            if (startDelayRef.current) clearTimeout(startDelayRef.current);
        };
    }, [openIndex]);

    // Scroll-stagger reveal — orb header + cards fade in as the section
    // enters the viewport. Uses GSAP context so it cleans up correctly.
    useEffect(() => {
        const ctx = gsap.context(() => {
            gsap.fromTo('.aif-orb-wrap > *', { y: 24, opacity: 0 }, {
                y: 0, opacity: 1, stagger: 0.12, duration: 0.9, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 80%' },
            });
            gsap.fromTo('.aif-card', { y: 28, opacity: 0 }, {
                y: 0, opacity: 1, stagger: 0.06, duration: 0.7, ease: 'power3.out',
                scrollTrigger: { trigger: ref.current, start: 'top 75%' },
            });
        }, ref);
        return () => ctx.revert();
    }, []);

    const handleCardClick = useCallback((i) => {
        setOpenIndex(prev => (prev === i ? null : i));
    }, []);

    const subtitle = openIndex === null
        ? 'Tap a question to hear the answer.'
        : (isTyping ? 'Web AI is answering…' : 'Tap another question, or tap again to dismiss.');

    return (
        <section className="faq-section ai-agent-faq" ref={ref}>
            <div className="faq-inner aif-inner">
                {/* Orb header */}
                <div className="aif-orb-wrap">
                    <div className={`aif-orb ${openIndex !== null ? 'aif-orb-active' : ''}`} aria-hidden="true">
                        <div className="aif-orb-glow" />
                        <div className="aif-orb-core" />
                        <div className="aif-orb-highlight" />
                        <div className="aif-orb-particles">
                            {[0, 1, 2, 3, 4, 5].map(i => (
                                <span key={i} className={`aif-particle aif-p${i}`} />
                            ))}
                        </div>
                    </div>
                    <span className="section-tag">FAQ</span>
                    <h2>Ask <span className="text-accent">Web AI</span></h2>
                    <p className="aif-subtitle">{subtitle}</p>
                </div>

                {/* Card grid */}
                <div className="aif-grid">
                    {faqData.map((item, i) => {
                        const isOpen = openIndex === i;
                        const isDimmed = openIndex !== null && !isOpen;
                        return (
                            <div
                                key={i}
                                className={`aif-card ${isOpen ? 'aif-card-open' : ''} ${isDimmed ? 'aif-card-dimmed' : ''}`}
                                onClick={() => handleCardClick(i)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        e.preventDefault();
                                        handleCardClick(i);
                                    }
                                }}
                                role="button"
                                tabIndex={0}
                                aria-expanded={isOpen}
                            >
                                <div className="aif-card-q">
                                    <span>{item.q}</span>
                                    <div className={`aif-card-icon ${isOpen ? 'aif-card-icon-open' : ''}`}>
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                                            <path d="M12 5v14" />
                                            <path d="M5 12h14" />
                                        </svg>
                                    </div>
                                </div>
                                {isOpen && (
                                    <div className="aif-card-a">
                                        <p>
                                            {typed}
                                            {isTyping && <span className="aif-cursor">|</span>}
                                            {!isTyping && typed === '' && (
                                                <span className="aif-thinking">
                                                    <span /><span /><span />
                                                </span>
                                            )}
                                        </p>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
};

// ============================================
// PRELOADER
// ============================================
const Preloader = ({ onComplete }) => {
    const preloaderRef = useRef(null);

    useEffect(() => {
        const tl = gsap.timeline({
            onComplete: () => {
                gsap.to(preloaderRef.current, {
                    yPercent: -100,
                    duration: 0.5,
                    ease: 'power4.inOut',
                    onComplete,
                });
            },
        });

        tl.fromTo('.preloader-logo',
            { scale: 0.8, opacity: 0 },
            { scale: 1, opacity: 1, duration: 0.5, ease: 'power2.out' }
        )
        .fromTo('.preloader-text',
            { opacity: 0, y: 15 },
            { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }, 0.3
        )
        .fromTo('.preloader-line',
            { scaleX: 0 },
            { scaleX: 1, duration: 0.5, ease: 'power3.inOut' }, 0.5
        )
        .to('.preloader-text', { opacity: 0, y: -10, duration: 0.2 }, 0.9);
    }, [onComplete]);

    return (
        <div className="preloader" ref={preloaderRef}>
            <div className="preloader-content">
                <img className="preloader-logo" src="/mfz-logo.webp" alt="Web AI" />
                <div className="preloader-text">Web AI</div>
                <div className="preloader-line" />
            </div>
        </div>
    );
};

// ============================================
// SCROLL PROGRESS BAR
// ============================================
const ScrollProgress = () => {
    const barRef = useRef(null);
    useEffect(() => {
        gsap.to(barRef.current, {
            scaleX: 1,
            ease: 'none',
            scrollTrigger: { trigger: 'body', start: 'top top', end: 'bottom bottom', scrub: 0.3 },
        });
    }, []);
    return <div className="scroll-progress" ref={barRef} />;
};

// ============================================
// MARQUEE STRIP
// ============================================
const MarqueeStrip = () => {
    const items = ['AI Powered', 'Built for Dubai', 'Under 60 Seconds', 'Web AI', 'One Click Deploy', 'Custom Domains', 'AI Powered', 'Built for Dubai', 'Under 60 Seconds', 'Web AI', 'One Click Deploy', 'Custom Domains'];
    return (
        <div className="marquee-strip">
            <div className="marquee-track">
                {items.map((text, i) => (
                    <span key={i} className="marquee-item">{text}<span className="marquee-dot">✦</span></span>
                ))}
            </div>
        </div>
    );
};

// ============================================
// STATS COUNTER
// ============================================
const StatsCounter = () => {
    const statsRef = useRef(null);
    useEffect(() => {
        const ctx = gsap.context(() => {
            gsap.utils.toArray('.stat-number').forEach((el) => {
                const target = parseInt(el.getAttribute('data-target'), 10);
                gsap.fromTo(el,
                    { textContent: 0 },
                    {
                        textContent: target,
                        duration: 2,
                        ease: 'power2.out',
                        snap: { textContent: 1 },
                        scrollTrigger: { trigger: el, start: 'top 85%' },
                    }
                );
            });
            gsap.fromTo('.stat-item',
                { y: 40, opacity: 0 },
                { y: 0, opacity: 1, stagger: 0.15, duration: 0.8, ease: 'power3.out',
                    scrollTrigger: { trigger: statsRef.current, start: 'top 85%' } }
            );
        }, statsRef);
        return () => ctx.revert();
    }, []);
    return (
        <section className="stats-section" ref={statsRef}>
            <img src="/glass-cubes.webp" alt="" className="stats-cubes stats-cubes-left" />
            <img src="/glass-cubes.webp" alt="" className="stats-cubes stats-cubes-right" />
            <div className="stats-inner">
                <div className="stat-item tilt-card glow-card">
                    <div className="stat-number-wrap"><span className="stat-number" data-target="500">0</span><span className="stat-suffix">+</span></div>
                    <div className="stat-label">Websites Generated</div>
                </div>
                <div className="stat-divider" />
                <div className="stat-item tilt-card glow-card">
                    <div className="stat-number-wrap"><span className="stat-number" data-target="200">0</span><span className="stat-suffix">+</span></div>
                    <div className="stat-label">Businesses Served</div>
                </div>
                <div className="stat-divider" />
                <div className="stat-item tilt-card glow-card">
                    <div className="stat-number-wrap"><span className="stat-prefix">&lt;</span><span className="stat-number" data-target="60">0</span><span className="stat-suffix">s</span></div>
                    <div className="stat-label">Average Build Time</div>
                </div>
                <div className="stat-divider" />
                <div className="stat-item tilt-card glow-card">
                    <div className="stat-number-wrap"><span className="stat-number" data-target="99">0</span><span className="stat-suffix">%</span></div>
                    <div className="stat-label">Uptime Guaranteed</div>
                </div>
            </div>
        </section>
    );
};

// ============================================
// REAL WEBSITE TEMPLATES FOR DEMO
// ============================================
const websites = [
    {
        prompt: 'Create a modern real estate agency website with property listings, hero section, and contact form...',
        html: `<div style="font-family:Inter,system-ui,sans-serif;color:#1a1a2e;background:#fff;">
  <nav style="display:flex;justify-content:space-between;align-items:center;padding:14px 24px;background:#fff;border-bottom:1px solid #eee;">
    <div style="font-weight:800;font-size:15px;color:#1a1a2e;">Prestige<span style="color:#c9a45c;">Realty</span></div>
    <div style="display:flex;gap:16px;font-size:11px;color:#666;">
      <span>Properties</span><span>About</span><span>Contact</span>
      <span style="background:#1a1a2e;color:#fff;padding:4px 12px;border-radius:4px;font-weight:600;">List Property</span>
    </div>
  </nav>
  <div style="display:flex;gap:20px;padding:28px 24px;align-items:center;">
    <div style="flex:1;">
      <div style="display:inline-block;background:#f0e6d3;color:#8a6914;font-size:9px;font-weight:700;padding:3px 10px;border-radius:20px;margin-bottom:10px;">PREMIUM LISTINGS</div>
      <div style="font-size:22px;font-weight:800;line-height:1.15;margin-bottom:8px;color:#1a1a2e;">Find Your Dream<br/>Home in Dubai</div>
      <div style="font-size:10px;color:#888;line-height:1.5;margin-bottom:14px;">Discover exclusive properties across Dubai's most prestigious neighborhoods. Luxury villas, penthouses, and waterfront residences.</div>
      <div style="display:flex;gap:8px;">
        <span style="background:#1a1a2e;color:#fff;padding:7px 16px;border-radius:6px;font-size:10px;font-weight:600;">Browse Properties</span>
        <span style="border:1px solid #ddd;padding:7px 16px;border-radius:6px;font-size:10px;color:#666;">Virtual Tours</span>
      </div>
    </div>
    <div style="flex:1;height:160px;border-radius:12px;display:flex;align-items:flex-end;padding:12px;position:relative;overflow:hidden;">
      <img src="https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&q=80" alt="Dubai skyline" loading="lazy" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;" />
      <div style="position:absolute;top:10px;right:10px;background:rgba(255,255,255,0.2);backdrop-filter:blur(4px);padding:3px 8px;border-radius:4px;font-size:8px;color:#fff;z-index:1;">360° Tour</div>
      <div style="background:rgba(0,0,0,0.45);backdrop-filter:blur(4px);padding:6px 10px;border-radius:6px;font-size:9px;color:#fff;z-index:1;"><strong>AED 4,500,000</strong><br/><span style="opacity:0.8;font-size:8px;">Palm Jumeirah Villa</span></div>
    </div>
  </div>
  <div style="padding:0 24px 20px;">
    <div style="font-size:13px;font-weight:700;margin-bottom:12px;color:#1a1a2e;">Featured Properties</div>
    <div style="display:flex;gap:10px;">
      <div style="flex:1;border:1px solid #eee;border-radius:10px;overflow:hidden;">
        <div style="height:65px;position:relative;"><img src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&q=80" alt="Marina Penthouse" style="width:100%;height:100%;object-fit:cover;" /></div>
        <div style="padding:8px;">
          <div style="font-size:10px;font-weight:700;">Marina Penthouse</div>
          <div style="font-size:9px;color:#888;margin:2px 0;">Dubai Marina · 3 Bed</div>
          <div style="font-size:10px;font-weight:800;color:#c9a45c;">AED 2,800,000</div>
        </div>
      </div>
      <div style="flex:1;border:1px solid #eee;border-radius:10px;overflow:hidden;">
        <div style="height:65px;position:relative;"><img src="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&q=80" alt="Creek Harbour Apt" style="width:100%;height:100%;object-fit:cover;" /></div>
        <div style="padding:8px;">
          <div style="font-size:10px;font-weight:700;">Creek Harbour Apt</div>
          <div style="font-size:9px;color:#888;margin:2px 0;">Dubai Creek · 2 Bed</div>
          <div style="font-size:10px;font-weight:800;color:#c9a45c;">AED 1,650,000</div>
        </div>
      </div>
      <div style="flex:1;border:1px solid #eee;border-radius:10px;overflow:hidden;">
        <div style="height:65px;position:relative;"><img src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&q=80" alt="JBR Beachfront" style="width:100%;height:100%;object-fit:cover;" /></div>
        <div style="padding:8px;">
          <div style="font-size:10px;font-weight:700;">JBR Beachfront</div>
          <div style="font-size:9px;color:#888;margin:2px 0;">JBR Walk · 4 Bed</div>
          <div style="font-size:10px;font-weight:800;color:#c9a45c;">AED 5,200,000</div>
        </div>
      </div>
    </div>
  </div>
  <div style="background:#1a1a2e;padding:12px 24px;display:flex;justify-content:space-between;align-items:center;">
    <span style="color:#fff;font-size:9px;font-weight:600;">Prestige Realty © 2026</span>
    <div style="display:flex;gap:12px;font-size:8px;color:#888;"><span>Privacy</span><span>Terms</span><span>Contact</span></div>
  </div>
</div>`,
    },
    {
        prompt: 'Build a luxury restaurant website with menu showcase, reservation system, and dark elegant theme...',
        html: `<div style="font-family:Georgia,serif;color:#e8d5b5;background:#0f0f0f;">
  <nav style="display:flex;justify-content:space-between;align-items:center;padding:16px 24px;border-bottom:1px solid #222;">
    <div style="font-size:15px;letter-spacing:3px;font-weight:400;color:#e8d5b5;">SAFFRON</div>
    <div style="display:flex;gap:16px;font-size:10px;letter-spacing:1px;color:#888;">
      <span>MENU</span><span>STORY</span><span>GALLERY</span>
      <span style="background:#c9a45c;color:#0f0f0f;padding:4px 14px;border-radius:2px;font-weight:700;font-family:system-ui;">Reserve</span>
    </div>
  </nav>
  <div style="text-align:center;padding:0;position:relative;">
    <div style="position:relative;height:180px;overflow:hidden;">
      <img src="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80" alt="Fine dining" loading="lazy" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.35);" />
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;">
        <div style="font-size:9px;letter-spacing:4px;color:#c9a45c;margin-bottom:10px;">FINE DINING EXPERIENCE</div>
        <div style="font-size:26px;font-weight:400;line-height:1.2;margin-bottom:10px;color:#fff;">Where Culinary Art<br/>Meets Elegance</div>
        <div style="font-size:10px;color:#ccc;line-height:1.6;max-width:340px;margin:0 auto 16px;font-style:italic;">An exquisite journey through Middle Eastern flavors, reimagined with modern French techniques by Chef Ahmad Khalil.</div>
        <div style="display:inline-flex;gap:8px;">
          <span style="background:#c9a45c;color:#0f0f0f;padding:7px 20px;border-radius:2px;font-size:10px;font-weight:700;font-family:system-ui;">Book a Table</span>
          <span style="border:1px solid rgba(255,255,255,0.3);padding:7px 20px;border-radius:2px;font-size:10px;color:#ddd;font-family:system-ui;">View Menu</span>
        </div>
      </div>
    </div>
  </div>
  <div style="padding:24px;">
    <div style="text-align:center;font-size:9px;letter-spacing:3px;color:#c9a45c;margin-bottom:14px;">SIGNATURE DISHES</div>
    <div style="display:flex;gap:10px;">
      <div style="flex:1;background:#1a1a1a;border-radius:8px;overflow:hidden;border:1px solid #222;">
        <div style="height:70px;position:relative;"><img src="https://images.unsplash.com/photo-1544025162-d76694265947?w=400&q=80" alt="Lamb Shank" style="width:100%;height:100%;object-fit:cover;" /></div>
        <div style="padding:10px;">
          <div style="font-size:11px;color:#fff;margin-bottom:2px;">Saffron Lamb Shank</div>
          <div style="font-size:8px;color:#888;font-style:italic;margin-bottom:4px;">Slow-braised 8hrs, rose petal jus</div>
          <div style="font-size:11px;color:#c9a45c;font-weight:700;font-family:system-ui;">AED 185</div>
        </div>
      </div>
      <div style="flex:1;background:#1a1a1a;border-radius:8px;overflow:hidden;border:1px solid #222;">
        <div style="height:70px;position:relative;"><img src="https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400&q=80" alt="Truffle Hummus" style="width:100%;height:100%;object-fit:cover;" /></div>
        <div style="padding:10px;">
          <div style="font-size:11px;color:#fff;margin-bottom:2px;">Truffle Hummus</div>
          <div style="font-size:8px;color:#888;font-style:italic;margin-bottom:4px;">Black truffle, smoked paprika oil</div>
          <div style="font-size:11px;color:#c9a45c;font-weight:700;font-family:system-ui;">AED 95</div>
        </div>
      </div>
      <div style="flex:1;background:#1a1a1a;border-radius:8px;overflow:hidden;border:1px solid #222;">
        <div style="height:70px;position:relative;"><img src="https://images.unsplash.com/photo-1579372786545-d24232daf58c?w=400&q=80" alt="Pistachio Kunafa" style="width:100%;height:100%;object-fit:cover;" /></div>
        <div style="padding:10px;">
          <div style="font-size:11px;color:#fff;margin-bottom:2px;">Pistachio Kunafa</div>
          <div style="font-size:8px;color:#888;font-style:italic;margin-bottom:4px;">Crispy phyllo, orange blossom cream</div>
          <div style="font-size:11px;color:#c9a45c;font-weight:700;font-family:system-ui;">AED 65</div>
        </div>
      </div>
    </div>
  </div>
  <div style="background:#0a0a0a;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #1a1a1a;">
    <span style="font-size:9px;letter-spacing:2px;color:#555;">SAFFRON © 2026</span>
    <div style="display:flex;gap:12px;font-size:8px;color:#555;"><span>DIFC, Dubai</span><span>+971 4 555 0000</span></div>
  </div>
</div>`,
    },
    {
        prompt: 'Design a fitness studio website with class schedules, trainer profiles, and energetic bold design...',
        html: `<div style="font-family:system-ui,sans-serif;color:#fff;background:#111;">
  <nav style="display:flex;justify-content:space-between;align-items:center;padding:14px 24px;background:#111;">
    <div style="font-size:16px;font-weight:900;letter-spacing:-0.5px;">APEX<span style="color:#ff4d4d;">FIT</span></div>
    <div style="display:flex;gap:16px;font-size:10px;font-weight:600;color:#999;align-items:center;">
      <span>Classes</span><span>Trainers</span><span>Plans</span>
      <span style="background:#ff4d4d;color:#fff;padding:5px 14px;border-radius:6px;font-weight:700;">Join Now</span>
    </div>
  </nav>
  <div style="display:flex;gap:20px;padding:28px 24px;align-items:center;">
    <div style="flex:1;">
      <div style="display:inline-block;background:rgba(255,77,77,0.15);color:#ff4d4d;font-size:9px;font-weight:800;padding:3px 10px;border-radius:20px;margin-bottom:10px;letter-spacing:1px;">NO EXCUSES</div>
      <div style="font-size:24px;font-weight:900;line-height:1.1;margin-bottom:8px;">Transform Your<br/>Body & Mind</div>
      <div style="font-size:10px;color:#777;line-height:1.6;margin-bottom:14px;">Dubai's premier fitness studio. Expert trainers, 50+ weekly classes, and state-of-the-art equipment.</div>
      <div style="display:flex;gap:8px;">
        <span style="background:#ff4d4d;color:#fff;padding:8px 18px;border-radius:8px;font-size:10px;font-weight:700;">Start Free Trial</span>
        <span style="border:1px solid #333;padding:8px 18px;border-radius:8px;font-size:10px;color:#999;">View Schedule</span>
      </div>
      <div style="display:flex;gap:20px;margin-top:16px;">
        <div><div style="font-size:18px;font-weight:900;color:#ff4d4d;">50+</div><div style="font-size:8px;color:#666;">Weekly Classes</div></div>
        <div><div style="font-size:18px;font-weight:900;">15</div><div style="font-size:8px;color:#666;">Expert Trainers</div></div>
        <div><div style="font-size:18px;font-weight:900;">2K+</div><div style="font-size:8px;color:#666;">Active Members</div></div>
      </div>
    </div>
    <div style="flex:1;height:180px;border-radius:14px;position:relative;overflow:hidden;">
      <img src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600&q=80" alt="Gym interior" loading="lazy" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.6);" />
      <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
        <div style="font-size:48px;font-weight:900;opacity:0.25;color:#fff;">APEX</div>
      </div>
      <div style="position:absolute;bottom:10px;left:10px;right:10px;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);padding:6px 10px;border-radius:6px;display:flex;justify-content:space-between;align-items:center;">
        <div><div style="font-size:9px;font-weight:700;">Next Class: HIIT Blast</div><div style="font-size:8px;color:#999;">Today 6:00 PM · Coach Sarah</div></div>
        <span style="background:#ff4d4d;padding:3px 8px;border-radius:4px;font-size:8px;font-weight:700;">Book</span>
      </div>
    </div>
  </div>
  <div style="padding:0 24px 20px;">
    <div style="font-size:13px;font-weight:800;margin-bottom:12px;">Popular Classes</div>
    <div style="display:flex;gap:10px;">
      <div style="flex:1;background:#1a1a1a;border-radius:10px;overflow:hidden;border:1px solid #222;">
        <div style="height:55px;position:relative;"><img src="https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=400&q=80" alt="Boxing" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.7);" /></div>
        <div style="padding:10px;">
          <div style="font-size:11px;font-weight:700;">Boxing</div>
          <div style="font-size:8px;color:#777;margin:2px 0;">Mon/Wed/Fri · 7AM</div>
          <div style="font-size:9px;color:#ff4d4d;font-weight:700;margin-top:4px;">8 spots left</div>
        </div>
      </div>
      <div style="flex:1;background:#1a1a1a;border-radius:10px;overflow:hidden;border:1px solid #222;">
        <div style="height:55px;position:relative;"><img src="https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&q=80" alt="Yoga" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.7);" /></div>
        <div style="padding:10px;">
          <div style="font-size:11px;font-weight:700;">Power Yoga</div>
          <div style="font-size:8px;color:#777;margin:2px 0;">Daily · 6:30AM</div>
          <div style="font-size:9px;color:#ff4d4d;font-weight:700;margin-top:4px;">5 spots left</div>
        </div>
      </div>
      <div style="flex:1;background:#1a1a1a;border-radius:10px;overflow:hidden;border:1px solid #222;">
        <div style="height:55px;position:relative;"><img src="https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&q=80" alt="CrossFit" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.7);" /></div>
        <div style="padding:10px;">
          <div style="font-size:11px;font-weight:700;">CrossFit</div>
          <div style="font-size:8px;color:#777;margin:2px 0;">Tue/Thu/Sat · 5PM</div>
          <div style="font-size:9px;color:#ff4d4d;font-weight:700;margin-top:4px;">3 spots left</div>
        </div>
      </div>
    </div>
  </div>
  <div style="background:#0a0a0a;padding:12px 24px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #1a1a1a;">
    <span style="font-size:9px;font-weight:700;color:#555;">APEXFIT © 2026</span>
    <div style="display:flex;gap:12px;font-size:8px;color:#555;"><span>Business Bay, Dubai</span><span>info@apexfit.ae</span></div>
  </div>
</div>`,
    },
];

// ============================================
// INTERACTIVE GENERATOR DEMO
// ============================================
const GeneratorDemo = () => {
    const [phase, setPhase] = useState('idle');
    const [typedText, setTypedText] = useState('');
    const [progress, setProgress] = useState(0);
    const [currentPromptIndex, setCurrentPromptIndex] = useState(0);
    const [siteVisible, setSiteVisible] = useState(false); // eslint-disable-line no-unused-vars
    const demoRef = useRef(null);
    const iframeRef = useRef(null);
    const timeoutsRef = useRef([]);

    const site = websites[currentPromptIndex % websites.length];

    const clearAllTimeouts = useCallback(() => {
        timeoutsRef.current.forEach(id => clearTimeout(id));
        timeoutsRef.current = [];
    }, []);

    const addTimeout = useCallback((fn, delay) => {
        const id = setTimeout(fn, delay);
        timeoutsRef.current.push(id);
        return id;
    }, []);

    const runCycle = useCallback(() => {
        const prompt = site.prompt;
        let charIndex = 0;

        setPhase('typing');
        setTypedText('');
        setProgress(0);
        setSiteVisible(false);

        const typeInterval = setInterval(() => {
            charIndex++;
            if (charIndex <= prompt.length) {
                setTypedText(prompt.slice(0, charIndex));
            } else {
                clearInterval(typeInterval);
                addTimeout(() => {
                    setPhase('generating');
                    let prog = 0;
                    const progInterval = setInterval(() => {
                        prog += Math.random() * 12 + 4;
                        if (prog >= 100) {
                            prog = 100;
                            clearInterval(progInterval);
                            addTimeout(() => {
                                setPhase('building');
                                // Write real HTML into iframe
                                const iframe = iframeRef.current;
                                if (iframe) {
                                    const doc = iframe.contentDocument || iframe.contentWindow?.document;
                                    if (doc) {
                                        doc.open();
                                        doc.write(`<!DOCTYPE html><html><head><style>
                                            *{margin:0;padding:0;box-sizing:border-box;}
                                            body{opacity:0;transition:opacity 0.6s ease;}
                                            body.show{opacity:1;}
                                        </style></head><body>${site.html}<script>
                                            setTimeout(()=>document.body.classList.add('show'),50);
                                        </script></body></html>`);
                                        doc.close();
                                    }
                                }
                                addTimeout(() => setSiteVisible(true), 100);
                                addTimeout(() => {
                                    setPhase('done');
                                    addTimeout(() => setCurrentPromptIndex(prev => prev + 1), 4000);
                                }, 1200);
                            }, 400);
                        }
                        setProgress(Math.min(prog, 100));
                    }, 120);
                    timeoutsRef.current.push(progInterval);
                }, 600);
            }
        }, 25);
        timeoutsRef.current.push(typeInterval);
    }, [site, addTimeout]);

    useEffect(() => {
        clearAllTimeouts();
        runCycle();
        return clearAllTimeouts;
    }, [currentPromptIndex, runCycle, clearAllTimeouts]);

    return (
        <div className="demo-browser" ref={demoRef}>
            <div className="browser-chrome">
                <div className="browser-dots"><span className="dot red" /><span className="dot yellow" /><span className="dot green" /></div>
                <div className="browser-url">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#27C93F" strokeWidth="2.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>generator.meydanfz.ae</span>
                    <div className={`browser-live-dot ${phase === 'done' ? 'live' : ''}`} />
                </div>
            </div>

            <div className="browser-body">
                {/* Sidebar */}
                <div className="demo-sidebar">
                    <div className="demo-sidebar-head">
                        <div className="demo-avatar">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                        </div>
                        <span className="demo-sidebar-label">Your Prompt</span>
                    </div>

                    <div className="demo-prompt-box">
                        <span className="demo-typed">{typedText}</span>
                        {phase === 'typing' && <span className="demo-cursor">|</span>}
                    </div>

                    <button className={`demo-gen-btn ${phase === 'generating' ? 'loading' : ''} ${phase === 'building' || phase === 'done' ? 'success' : ''}`}>
                        {phase === 'generating' ? (<><span className="demo-spinner" />Generating...</>) :
                         phase === 'building' || phase === 'done' ? (<><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>Generated</>) :
                         (<><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/></svg>Generate Website</>)}
                    </button>

                    {phase === 'generating' && (
                        <div className="demo-progress-wrap">
                            <div className="demo-progress-bar"><div className="demo-progress-fill" style={{ width: `${progress}%` }} /></div>
                            <span className="demo-progress-text">{Math.round(progress)}%</span>
                        </div>
                    )}

                    <div className="demo-status-feed">
                        {phase === 'generating' && progress < 35 && <div className="demo-status-item active"><span className="demo-status-dot pulse" />Analyzing prompt...</div>}
                        {phase === 'generating' && progress >= 35 && progress < 65 && <div className="demo-status-item active"><span className="demo-status-dot pulse" />Generating layout...</div>}
                        {phase === 'generating' && progress >= 65 && progress < 90 && <div className="demo-status-item active"><span className="demo-status-dot pulse" />Writing HTML & CSS...</div>}
                        {phase === 'generating' && progress >= 90 && <div className="demo-status-item active"><span className="demo-status-dot pulse" />Adding content...</div>}
                        {phase === 'building' && <div className="demo-status-item active"><span className="demo-status-dot pulse" />Rendering preview...</div>}
                        {phase === 'done' && <div className="demo-status-item done"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5ED1AD" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>Website ready</div>}
                    </div>
                </div>

                {/* Preview: Real website in iframe */}
                <div className="demo-preview">
                    {(phase === 'idle' || phase === 'typing') && (
                        <div className="demo-empty-state">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#D1D8DA" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                            <span>Preview will appear here</span>
                        </div>
                    )}
                    {phase === 'generating' && (
                        <div className="demo-skeleton">
                            <div className="skel skel-nav shimmer" />
                            <div className="skel skel-hero-block shimmer" />
                            <div className="skel-row">
                                <div className="skel skel-card shimmer" />
                                <div className="skel skel-card shimmer" style={{ animationDelay: '0.15s' }} />
                                <div className="skel skel-card shimmer" style={{ animationDelay: '0.3s' }} />
                            </div>
                            <div className="skel skel-section shimmer" style={{ animationDelay: '0.2s' }} />
                            <div className="skel skel-footer shimmer" style={{ animationDelay: '0.35s' }} />
                        </div>
                    )}
                    <iframe
                        ref={iframeRef}
                        title="Generated Website Preview"
                        className={`demo-iframe ${(phase === 'building' || phase === 'done') ? 'visible' : ''}`}
                        sandbox="allow-scripts allow-same-origin"
                    />
                </div>
            </div>
        </div>
    );
};


// ============================================
// LANDING PAGE
// ============================================
const LandingPage = () => {
    const heroRef = useRef(null);
    const showcaseRef = useRef(null);
    const ctaRef = useRef(null);
    const hiwPinRef = useRef(null);
    const [loaded, setLoaded] = useState(false);
    const [videoEnded, setVideoEnded] = useState(false);
    const videoRef = useRef(null);

    // Lenis smooth scroll
    useEffect(() => {
        const lenis = new Lenis({
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            smoothWheel: true,
        });
        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((time) => lenis.raf(time * 1000));
        gsap.ticker.lagSmoothing(0);
        return () => {
            gsap.ticker.remove(lenis.raf);
            lenis.destroy();
        };
    }, []);

    useEffect(() => {
        if (!loaded) return;
        const ctx = gsap.context(() => {
            // Hero entrance — just fade in the video
            gsap.fromTo('.hero-img-wrapper', { opacity: 0 }, { opacity: 1, duration: 0.5, ease: 'power3.out' });

            // Showcase browser entrance
            gsap.fromTo('.demo-browser',
                { y: 120, opacity: 0, scale: 0.92 },
                { y: 0, opacity: 1, scale: 1, duration: 1.4, ease: 'power3.out',
                    scrollTrigger: { trigger: showcaseRef.current, start: 'top 75%' }
                }
            );

            gsap.fromTo('.showcase-heading > *',
                { y: 50, opacity: 0 },
                { y: 0, opacity: 1, stagger: 0.12, duration: 0.9, ease: 'power3.out',
                    scrollTrigger: { trigger: showcaseRef.current, start: 'top 80%' }
                }
            );

            // =============================================
            // HOW IT WORKS — PINNED CINEMATIC SCROLL
            // =============================================
            if (hiwPinRef.current) {
                // Heading entrance
                gsap.fromTo('.hiw-pin-header > *',
                    { y: 40, opacity: 0 },
                    { y: 0, opacity: 1, stagger: 0.1, duration: 0.8, ease: 'power3.out',
                        scrollTrigger: { trigger: '.hiw-pin-header', start: 'top 85%' } }
                );

                const hiwTl = gsap.timeline({
                    scrollTrigger: {
                        trigger: hiwPinRef.current,
                        start: 'top top',
                        end: '+=200%',
                        pin: true,
                        scrub: 1,
                        anticipatePin: 1,
                    }
                });

                // -- ACT 1: Typing the prompt (0% → 28%) --
                hiwTl.fromTo('.hiw-typing-mask',
                    { clipPath: 'inset(0 100% 0 0)' },
                    { clipPath: 'inset(0 0% 0 0)', duration: 0.20, ease: 'none' }, 0.02
                );
                hiwTl.to('.hiw-mock-cursor', { autoAlpha: 0, duration: 0.01 }, 0.22);
                hiwTl.to('.hiw-gen-btn-mock', {
                    backgroundColor: '#08292E', color: '#fff', borderColor: '#08292E', duration: 0.03
                }, 0.23);
                hiwTl.fromTo('.hiw-gen-btn-mock .hiw-btn-spinner',
                    { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.02 }, 0.25
                );

                // -- TRANSITION 1 → 2 (28% → 35%) --
                hiwTl.to('.hiw-act-1', { autoAlpha: 0, y: -20, duration: 0.04 }, 0.28);
                hiwTl.to('.hiw-frame-1', { autoAlpha: 0, duration: 0.04 }, 0.28);
                hiwTl.to('.hiw-dot-1', { scale: 0.8, opacity: 0.3, duration: 0.03 }, 0.28);
                hiwTl.to('.hiw-line-fill-1', { scaleY: 1, duration: 0.04 }, 0.28);
                hiwTl.fromTo('.hiw-act-2', { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.04 }, 0.34);
                hiwTl.fromTo('.hiw-frame-2', { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.04 }, 0.34);
                hiwTl.to('.hiw-dot-2', { background: '#5ED1AD', scale: 1.15, boxShadow: '0 0 12px rgba(94,209,173,0.5)', duration: 0.03 }, 0.34);

                // -- ACT 2: Selection + toolbar (35% → 58%) --
                hiwTl.fromTo('.hiw-select-border',
                    { opacity: 0 }, { opacity: 1, duration: 0.08 }, 0.38
                );
                hiwTl.fromTo('.hiw-edit-toolbar',
                    { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.06 }, 0.46
                );

                // -- TRANSITION 2 → 3 (58% → 65%) --
                hiwTl.to('.hiw-act-2', { autoAlpha: 0, y: -20, duration: 0.04 }, 0.58);
                hiwTl.to('.hiw-frame-2', { autoAlpha: 0, duration: 0.04 }, 0.58);
                hiwTl.to('.hiw-dot-2', { scale: 0.8, opacity: 0.3, boxShadow: 'none', duration: 0.03 }, 0.58);
                hiwTl.to('.hiw-line-fill-2', { scaleY: 1, duration: 0.04 }, 0.58);
                hiwTl.fromTo('.hiw-act-3', { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.04 }, 0.64);
                hiwTl.fromTo('.hiw-frame-3', { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.04 }, 0.64);
                hiwTl.to('.hiw-dot-3', { background: '#5ED1AD', scale: 1.15, boxShadow: '0 0 12px rgba(94,209,173,0.5)', duration: 0.03 }, 0.64);

                // -- ACT 3: Deploy progress (65% → 100%) --
                hiwTl.fromTo('.hiw-deploy-fill',
                    { width: '0%' },
                    { width: '100%', duration: 0.20, ease: 'power1.inOut' }, 0.68
                );
                hiwTl.fromTo('.hiw-deploy-percent',
                    { textContent: '0' },
                    { textContent: '100', duration: 0.20, ease: 'power1.inOut', snap: { textContent: 1 },
                      modifiers: { textContent: (v) => Math.round(v) + '%' } }, 0.68
                );
                hiwTl.fromTo('.hiw-deploy-success',
                    { autoAlpha: 0, y: 10, scale: 0.9 },
                    { autoAlpha: 1, y: 0, scale: 1, duration: 0.06, ease: 'back.out(2)' }, 0.92
                );
            }

            // CTA
            gsap.fromTo('.cta-inner > *',
                { y: 40, opacity: 0 },
                { y: 0, opacity: 1, stagger: 0.15, duration: 0.9, ease: 'power3.out',
                    scrollTrigger: { trigger: ctaRef.current, start: 'top 80%' } }
            );

            // =============================================
            // FLOATING ELEMENTS PARALLAX
            // =============================================
            gsap.utils.toArray('.float-circle').forEach((el) => {
                const speed = parseFloat(el.getAttribute('data-speed')) || 0.5;
                gsap.to(el, {
                    y: () => speed * 200,
                    ease: 'none',
                    scrollTrigger: { trigger: el.closest('section') || el.parentElement, start: 'top bottom', end: 'bottom top', scrub: true },
                });
            });

            // =============================================
            // SPLIT WORDS REVEAL
            // =============================================
            gsap.utils.toArray('.split-words .word').forEach((word) => {
                gsap.fromTo(word, { y: '100%', opacity: 0 }, {
                    y: '0%', opacity: 1, duration: 0.8, ease: 'power3.out',
                    scrollTrigger: { trigger: word.closest('section') || word, start: 'top 85%' }
                });
            });

        }, heroRef);

        // =============================================
        // 3D TILT CARDS (non-GSAP listeners)
        // =============================================
        const tiltEls = document.querySelectorAll('.tilt-card');
        const tiltHandlers = [];
        const isTouchDevice = window.matchMedia('(hover: none)').matches;
        if (!isTouchDevice) {
            tiltEls.forEach((el) => {
                const onMove = (e) => {
                    const rect = el.getBoundingClientRect();
                    const x = (e.clientX - rect.left) / rect.width - 0.5;
                    const y = (e.clientY - rect.top) / rect.height - 0.5;
                    gsap.to(el, {
                        rotateY: x * 16, rotateX: -y * 16,
                        boxShadow: `${-x * 10}px ${y * 10}px 30px rgba(8,41,46,0.1)`,
                        duration: 0.4, ease: 'power3.out',
                    });
                };
                const onLeave = () => {
                    gsap.to(el, { rotateY: 0, rotateX: 0, boxShadow: '0 4px 20px rgba(8,41,46,0.06)', duration: 0.7, ease: 'elastic.out(1, 0.3)' });
                };
                el.style.perspective = '800px';
                el.style.transformStyle = 'preserve-3d';
                el.addEventListener('mousemove', onMove);
                el.addEventListener('mouseleave', onLeave);
                tiltHandlers.push({ el, onMove, onLeave });
            });
        }

        // =============================================
        // HOVER GLOW CARDS (CSS var driven)
        // =============================================
        const glowEls = document.querySelectorAll('.glow-card');
        const glowHandlers = [];
        if (!isTouchDevice) {
            glowEls.forEach((el) => {
                const onMove = (e) => {
                    const rect = el.getBoundingClientRect();
                    el.style.setProperty('--glow-x', `${e.clientX - rect.left}px`);
                    el.style.setProperty('--glow-y', `${e.clientY - rect.top}px`);
                };
                el.addEventListener('mousemove', onMove);
                glowHandlers.push({ el, onMove });
            });
        }

        return () => {
            ctx.revert();
            tiltHandlers.forEach(({ el, onMove, onLeave }) => {
                el.removeEventListener('mousemove', onMove);
                el.removeEventListener('mouseleave', onLeave);
            });
            glowHandlers.forEach(({ el, onMove }) => {
                el.removeEventListener('mousemove', onMove);
            });
        };
    }, [loaded]);

    // Start video only after preloader finishes, then transition after it ends
    const videoEndedRef = useRef(false);
    useEffect(() => {
        if (!loaded) return;
        const vid = videoRef.current;
        if (!vid || videoEndedRef.current) return;
        vid.currentTime = 0;
        // Ensure muted (required for mobile autoplay)
        vid.muted = true;
        vid.setAttribute('playsinline', '');
        vid.setAttribute('webkit-playsinline', '');
        const tryPlay = () => {
            vid.play().catch(() => {
                // Retry once after a short delay (mobile sometimes needs a tick)
                setTimeout(() => {
                    vid.play().catch(() => {
                        videoEndedRef.current = true;
                        setVideoEnded(true);
                    });
                }, 300);
            });
        };
        // If video data is ready, play immediately; otherwise wait for canplay
        if (vid.readyState >= 3) {
            tryPlay();
        } else {
            vid.addEventListener('canplay', tryPlay, { once: true });
        }
        // Fallback timer in case onEnded doesn't fire
        const timer = setTimeout(() => {
            if (!videoEndedRef.current) {
                videoEndedRef.current = true;
                setVideoEnded(true);
            }
        }, 8000);
        return () => clearTimeout(timer);
    }, [loaded]);

    // Animate hero content when video ends and image appears
    useEffect(() => {
        if (!videoEnded) return;
        const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
        tl
            .fromTo('.hero-content-image .hero-tag', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, 0.2)
            .fromTo('.hero-content-image .hero-title-line', { y: 50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, stagger: 0.12 }, 0.3)
            .fromTo('.hero-content-image .hero-subtitle', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, 0.7)
            .fromTo('.hero-scroll-indicator', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, 0.9);
    }, [videoEnded]);

    return (
        <>
        {!loaded && <Preloader onComplete={() => setLoaded(true)} />}
        <ScrollProgress />
        <div className="landing" ref={heroRef}>
            {/* HERO */}
            <section className="hero">
                <div className="hero-img-wrapper">
                    <video
                        ref={videoRef}
                        className={`hero-video${videoEnded ? ' hero-video-hidden' : ''}`}
                        src="/Fawri-vid-opt.mp4"
                        autoPlay
                        muted
                        playsInline
                        preload="auto"
                        onEnded={() => {
                            if (!videoEndedRef.current) {
                                videoEndedRef.current = true;
                                setVideoEnded(true);
                            }
                        }}
                    />
                    <img
                        src="/hero-bg.webp"
                        alt="Web AI Dubai Skyline"
                        className={`hero-fallback-img${videoEnded ? ' hero-fallback-visible' : ''}`}
                    />
                </div>
                <div className="hero-overlay" />
                <FloatingElements section="hero" />
                {!videoEnded && (
                    <div className="hero-video-text">
                        <h1 className="hero-video-headline">From Idea to Website<br /><span>In Seconds.</span></h1>
                    </div>
                )}
                <div className={`hero-content hero-content-centered${videoEnded ? ' hero-content-image' : ''}`}>
                    {videoEnded && (
                        <>
                            <div className="hero-tag"><span className="tag-dot" />Web AI</div>
                            <h1 className="hero-title">
                                <span className="hero-title-line"><SplitWords>AI-Powered Websites</SplitWords></span>
                                <span className="hero-title-line hero-title-accent"><SplitWords>For Your Business.</SplitWords></span>
                            </h1>
                            <p className="hero-subtitle">
                                Describe your business, and our AI builds you a professional website in seconds.
                                Chat to edit, refine, and publish — no coding required.
                            </p>
                        </>
                    )}
                    {videoEnded && (
                        <div className="hero-cta hero-cta-fadein">
                            <MagneticButton>
                                <Link to="/signup" className="btn-primary">
                                    Get Started
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                                </Link>
                            </MagneticButton>
                        </div>
                    )}
                </div>
            </section>

            {/* SHOWCASE */}
            <section className="showcase" id="showcase" ref={showcaseRef}>
                <div className="showcase-inner">
                    <div className="showcase-heading">
                        <span className="section-tag">See It In Action</span>
                        <h2>Describe It. <span className="text-accent">We Build It.</span></h2>
                        <p>Watch our AI generate a complete website from a single prompt — live.</p>
                    </div>
                    <GeneratorDemo />
                </div>
            </section>

            {/* MARQUEE */}
            <MarqueeStrip />

            {/* STATS */}
            <StatsCounter />

            {/* COMPARISON */}
            <ComparisonSection />

            {/* HOW IT WORKS — HEADING */}
            <section className="hiw-intro" id="how-it-works">
                <div className="hiw-pin-header">
                    <span className="section-tag">How It Works</span>
                    <h2>Three Steps to <span className="text-accent">Your Website</span></h2>
                    <p className="hiw-pin-sub">Scroll down — watch it happen live</p>
                </div>
            </section>

            {/* HOW IT WORKS — PINNED EXPERIENCE */}
            <div className="hiw-pin" ref={hiwPinRef}>
                <div className="hiw-pin-layout">
                    {/* Left column — step info */}
                    <div className="hiw-info-col">
                        <div className="hiw-step-nav">
                            <div className="hiw-dot hiw-dot-1" />
                            <div className="hiw-dot-line"><div className="hiw-line-fill hiw-line-fill-1" /></div>
                            <div className="hiw-dot hiw-dot-2" />
                            <div className="hiw-dot-line"><div className="hiw-line-fill hiw-line-fill-2" /></div>
                            <div className="hiw-dot hiw-dot-3" />
                        </div>
                        <div className="hiw-acts">
                            <div className="hiw-act hiw-act-1">
                                <span className="hiw-act-num">01</span>
                                <h3>Describe Your Vision</h3>
                                <p>Type what you need in plain language. Our AI understands your industry, style preferences, and content — just like briefing a senior designer.</p>
                            </div>
                            <div className="hiw-act hiw-act-2" style={{visibility:'hidden',opacity:0}}>
                                <span className="hiw-act-num">02</span>
                                <h3>Refine Every Detail</h3>
                                <p>Click any element to edit it directly. Change text, colors, layouts — or send follow-up prompts to iterate until it's perfect.</p>
                            </div>
                            <div className="hiw-act hiw-act-3" style={{visibility:'hidden',opacity:0}}>
                                <span className="hiw-act-num">03</span>
                                <h3>Deploy Instantly</h3>
                                <p>One click and your website is live with a custom domain, SSL certificate, and global CDN — ready for your clients.</p>
                            </div>
                        </div>
                    </div>

                    {/* Right column — the screen */}
                    <div className="hiw-screen">
                        <div className="hiw-screen-chrome">
                            <div className="hiw-screen-dots"><span /><span /><span /></div>
                            <div className="hiw-screen-url">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#27C93F" strokeWidth="2.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                                generator.meydanfz.ae
                            </div>
                        </div>
                        <div className="hiw-screen-body">

                            {/* FRAME 1 — Prompt Interface */}
                            <div className="hiw-frame hiw-frame-1">
                                <div className="hiw-f-sidebar">
                                    <div className="hiw-f-head">
                                        <div className="hiw-f-avatar">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5ED1AD" strokeWidth="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                                        </div>
                                        <span>Your Prompt</span>
                                    </div>
                                    <div className="hiw-f-textarea">
                                        <div className="hiw-typing-mask">Create a modern real estate agency website with luxury property listings, Dubai skyline hero section, dark navy theme with gold accents, and an AED pricing display...</div>
                                        <span className="hiw-mock-cursor">|</span>
                                    </div>
                                    <button className="hiw-gen-btn-mock">
                                        <span className="hiw-btn-spinner" style={{visibility:'hidden',opacity:0}} />
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/></svg>
                                        Generate Website
                                    </button>
                                </div>
                                <div className="hiw-f-preview-empty">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#D1D8DA" strokeWidth="1"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                                    <span>Your website preview will appear here</span>
                                </div>
                            </div>

                            {/* FRAME 2 — Website + Editing */}
                            <div className="hiw-frame hiw-frame-2" style={{visibility:'hidden',opacity:0}}>
                                <div className="hiw-f-sidebar">
                                    <div className="hiw-f-head">
                                        <div className="hiw-f-avatar done">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                                        </div>
                                        <span>Editing</span>
                                    </div>
                                    <div className="hiw-f-iterations">
                                        <div className="hiw-f-iter done"><span className="hiw-iter-dot" />Initial generation</div>
                                        <div className="hiw-f-iter done"><span className="hiw-iter-dot" />Changed header to navy</div>
                                        <div className="hiw-f-iter active"><span className="hiw-iter-dot pulse" />Editing hero section...</div>
                                    </div>
                                </div>
                                <div className="hiw-f-website">
                                    {/* Mini real estate website */}
                                    <div className="hiw-ms">
                                        <div className="hiw-ms-nav">
                                            <span className="hiw-ms-logo">Prestige<em>Realty</em></span>
                                            <div className="hiw-ms-links"><span>Properties</span><span>About</span><span>Contact</span></div>
                                        </div>
                                        <div className="hiw-ms-hero">
                                            <img src="https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&q=60" alt="" className="hiw-ms-hero-img" loading="lazy" />
                                            <div className="hiw-ms-hero-overlay">
                                                <div className="hiw-ms-tag">PREMIUM LISTINGS</div>
                                                <div className="hiw-ms-h1">Find Your Dream<br/>Home in Dubai</div>
                                                <div className="hiw-ms-cta">Browse Properties →</div>
                                            </div>
                                            {/* Selection UI */}
                                            <div className="hiw-select-border">
                                                <div className="hiw-sel-handle tl" /><div className="hiw-sel-handle tr" />
                                                <div className="hiw-sel-handle bl" /><div className="hiw-sel-handle br" />
                                                <div className="hiw-sel-label">Hero Section</div>
                                            </div>
                                        </div>
                                        <div className="hiw-ms-cards">
                                            <div className="hiw-ms-card">
                                                <div className="hiw-ms-card-img"><img src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=200&q=60" alt="" loading="lazy" /></div>
                                                <div className="hiw-ms-card-info"><strong>Marina Penthouse</strong><span>AED 2,800,000</span></div>
                                            </div>
                                            <div className="hiw-ms-card">
                                                <div className="hiw-ms-card-img"><img src="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=200&q=60" alt="" loading="lazy" /></div>
                                                <div className="hiw-ms-card-info"><strong>Creek Harbour</strong><span>AED 1,650,000</span></div>
                                            </div>
                                            <div className="hiw-ms-card">
                                                <div className="hiw-ms-card-img"><img src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=200&q=60" alt="" loading="lazy" /></div>
                                                <div className="hiw-ms-card-info"><strong>JBR Beachfront</strong><span>AED 5,200,000</span></div>
                                            </div>
                                        </div>
                                    </div>
                                    {/* Floating edit toolbar */}
                                    <div className="hiw-edit-toolbar" style={{visibility:'hidden',opacity:0}}>
                                        <span className="hiw-et-btn">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>
                                            Edit Text
                                        </span>
                                        <span className="hiw-et-btn active">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="18" r="2.5"/></svg>
                                            Style
                                        </span>
                                        <span className="hiw-et-btn">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                                            Layout
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* FRAME 3 — Deploy */}
                            <div className="hiw-frame hiw-frame-3" style={{visibility:'hidden',opacity:0}}>
                                <div className="hiw-f-deploy-bg">
                                    <div className="hiw-ms">
                                        <div className="hiw-ms-nav"><span className="hiw-ms-logo">Prestige<em>Realty</em></span></div>
                                        <div style={{height:120,background:'linear-gradient(135deg,#1a1a2e,#2d2d5e)'}} />
                                        <div style={{display:'flex',gap:6,padding:10}}>
                                            <div style={{flex:1,height:50,background:'#f0f0f0',borderRadius:6}} />
                                            <div style={{flex:1,height:50,background:'#f0f0f0',borderRadius:6}} />
                                            <div style={{flex:1,height:50,background:'#f0f0f0',borderRadius:6}} />
                                        </div>
                                    </div>
                                </div>
                                <div className="hiw-f-deploy-overlay" />
                                <div className="hiw-f-deploy-modal">
                                    <div className="hiw-deploy-icon">
                                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5ED1AD" strokeWidth="1.5"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09Z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2Z"/></svg>
                                    </div>
                                    <h4>Deploying Your Website</h4>
                                    <div className="hiw-deploy-url">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5ED1AD" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>
                                        prestige-realty.meydanfz.ae
                                    </div>
                                    <div className="hiw-deploy-bar">
                                        <div className="hiw-deploy-fill" />
                                    </div>
                                    <div className="hiw-deploy-percent">0%</div>
                                    <div className="hiw-deploy-success" style={{visibility:'hidden',opacity:0}}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5ED1AD" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                                        <span>Your site is live!</span>
                                        <div className="hiw-live-badge"><span className="hiw-live-dot" />LIVE</div>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>
            </div>

            {/* HOW IT WORKS — SIMPLE MOBILE CARDS */}
            <div className="hiw-mobile">
                <div className="hiw-mobile-card">
                    <div className="hiw-mobile-num">01</div>
                    <div className="hiw-mobile-icon">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                    </div>
                    <h3>Describe Your Vision</h3>
                    <p>Type what you need in plain language. Our AI understands your industry and style — like briefing a designer.</p>
                </div>
                <div className="hiw-mobile-card">
                    <div className="hiw-mobile-num">02</div>
                    <div className="hiw-mobile-icon">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                    </div>
                    <h3>Refine Every Detail</h3>
                    <p>Click any element to edit directly. Change text, colors, layouts — or use follow-up prompts.</p>
                </div>
                <div className="hiw-mobile-card">
                    <div className="hiw-mobile-num">03</div>
                    <div className="hiw-mobile-icon">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                    </div>
                    <h3>Deploy Instantly</h3>
                    <p>One click — your site is live with a custom domain, SSL, and global CDN.</p>
                </div>
            </div>

            {/* TEMPLATE GALLERY */}
            <TemplateGallery />

            {/* CTA */}
            <section className="cta-section" ref={ctaRef} style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/cta-hands.webp)`, backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <FloatingElements section="cta" />
                <div className="cta-inner">
                    <h2><SplitWords>Ready to Build?</SplitWords></h2>
                    <p>Join businesses across Web AI already using AI to create professional websites.</p>
                    <MagneticButton>
                        <Link to="/signup" className="btn-primary large">
                            Create Your Website
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                        </Link>
                    </MagneticButton>
                </div>
            </section>

            {/* FAQ */}
            <FAQSection />

            {/* FOOTER */}
            <footer className="footer" style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/footer-skyline.webp)`, backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <div className="footer-inner">
                    <div className="footer-brand">
                        <Link to="/" className="footer-logo">
                            <img src="/mfz-logo.webp" alt="Web AI" className="footer-logo-img" />
                        </Link>
                        <p>AI-powered website generation platform. Build, customize, and deploy beautiful websites in minutes.</p>
                    </div>
                    <div className="footer-links">
                        <div className="footer-col"><h4>Platform</h4><a href="#showcase">Generator</a><a href="#how-it-works">How It Works</a></div>
                        <div className="footer-col"><h4>Company</h4><a href="https://meydanfz.ae" target="_blank" rel="noopener noreferrer">Web AI</a><a href="mailto:contact@meydanfz.ae">Contact</a></div>
                        <div className="footer-col"><h4>Legal</h4><a href="https://www.meydanfz.ae/terms-conditions" target="_blank" rel="noopener noreferrer">Terms &amp; Conditions</a><a href="https://www.meydanfz.ae/privacy-policy" target="_blank" rel="noopener noreferrer">Privacy Policy</a></div>
                    </div>
                </div>
                <div className="footer-bottom"><p>&copy; {new Date().getFullYear()} Web AI. All rights reserved.</p></div>
            </footer>
        </div>
        </>
    );
};

export default LandingPage;
